//! Forward HTTP `/api` traffic to the configured backend (streaming response body).

use axum::{
    body::Body,
    extract::Request,
    response::{IntoResponse, Response},
};
use futures_util::StreamExt;
use http::header::{CONNECTION, HOST, TRANSFER_ENCODING, UPGRADE};
use reqwest::Client;

const MAX_INBOUND_BODY: usize = 32 * 1024 * 1024;

pub fn build_upstream_client(accept_invalid_certs: bool) -> Result<Client, reqwest::Error> {
    let mut b = Client::builder().use_rustls_tls();
    if accept_invalid_certs {
        b = b.danger_accept_invalid_certs(true);
    }
    b.build()
}

fn skip_request_header(name: &http::HeaderName) -> bool {
    if name == HOST {
        return true;
    }
    matches!(
        name.as_str(),
        "connection" | "keep-alive" | "proxy-authenticate" | "proxy-authorization"
            | "te" | "trailer" | "transfer-encoding" | "upgrade"
    )
}

fn skip_response_header(name: &http::HeaderName) -> bool {
    matches!(
        name.as_str(),
        "connection" | "keep-alive" | "proxy-authenticate" | "proxy-authorization"
            | "te" | "trailer" | "transfer-encoding" | "upgrade"
    ) || name == CONNECTION
        || name == TRANSFER_ENCODING
        || name == UPGRADE
}

pub async fn proxy_http_request(
    client: &Client,
    backend_base: &str,
    req: Request<Body>,
) -> Response {
    let path_and_query = req
        .uri()
        .path_and_query()
        .map(|pq| pq.as_str())
        .unwrap_or("/");
    let url = format!("{backend_base}{path_and_query}");

    let method: reqwest::Method = req
        .method()
        .as_str()
        .parse()
        .unwrap_or(reqwest::Method::GET);

    let mut rb = client.request(method, &url);
    for (k, v) in req.headers().iter() {
        if skip_request_header(k) {
            continue;
        }
        if let Ok(val) = reqwest::header::HeaderValue::from_bytes(v.as_bytes()) {
            rb = rb.header(k.as_str(), val);
        }
    }

    let body_bytes = match axum::body::to_bytes(req.into_body(), MAX_INBOUND_BODY).await {
        Ok(b) => b,
        Err(e) => {
            return (
                http::StatusCode::BAD_GATEWAY,
                format!("read body: {e}"),
            )
                .into_response();
        }
    };

    let upstream = match rb.body(body_bytes).send().await {
        Ok(r) => r,
        Err(e) => {
            return (
                http::StatusCode::BAD_GATEWAY,
                format!("upstream: {e}"),
            )
                .into_response();
        }
    };

    let status = http::StatusCode::from_u16(upstream.status().as_u16())
        .unwrap_or(http::StatusCode::BAD_GATEWAY);

    let mut res = Response::builder().status(status);
    for (k, v) in upstream.headers().iter() {
        if skip_response_header(k) {
            continue;
        }
        res = res.header(k.as_str(), v.as_bytes());
    }

    let stream = upstream.bytes_stream().map(|chunk| {
        chunk.map_err(|_| std::io::Error::new(std::io::ErrorKind::Other, "upstream stream"))
    });
    let body = Body::from_stream(stream);
    match res.body(body) {
        Ok(r) => r,
        Err(_) => Response::new(Body::empty()),
    }
}
