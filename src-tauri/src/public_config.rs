//! Resolve upstream API origin using server-published `/api/public/client-config`.

use serde::Deserialize;

use crate::proxy_http;
use crate::settings;

#[derive(Debug, Deserialize)]
struct PublicClientConfigBody {
    desktop_backend_url: Option<String>,
}

/// If the public config returns a non-empty URL, use it; otherwise use bootstrap.
pub async fn resolve_upstream_base(
    bootstrap_origin: &str,
    accept_invalid_certs: bool,
) -> String {
    let client = match proxy_http::build_upstream_client(accept_invalid_certs) {
        Ok(c) => c,
        Err(_) => return bootstrap_origin.to_string(),
    };
    let url = format!(
        "{}/api/public/client-config",
        bootstrap_origin.trim_end_matches('/')
    );
    let resp = match client.get(&url).send().await {
        Ok(r) => r,
        Err(_) => return bootstrap_origin.to_string(),
    };
    if !resp.status().is_success() {
        return bootstrap_origin.to_string();
    }
    let body: PublicClientConfigBody = match resp.json().await {
        Ok(b) => b,
        Err(_) => return bootstrap_origin.to_string(),
    };
    let Some(raw) = body.desktop_backend_url else {
        return bootstrap_origin.to_string();
    };
    let t = raw.trim();
    if t.is_empty() {
        return bootstrap_origin.to_string();
    }
    settings::normalize_backend_url(t).unwrap_or_else(|_| bootstrap_origin.to_string())
}
