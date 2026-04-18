//! Loopback Axum server: static Vue `dist` + `/api` reverse proxy.

use axum::body::Body;
use axum::extract::{Request, State};
use axum::routing::any;
use axum::Router;
use std::net::SocketAddr;
use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::RwLock;
use tower_http::services::{ServeDir, ServeFile};

use crate::proxy_http;

#[derive(Clone)]
pub struct ServerState {
    pub client: reqwest::Client,
    pub backend_base: Arc<RwLock<String>>,
}

async fn proxy_api(
    State(state): State<ServerState>,
    req: Request<Body>,
) -> axum::response::Response {
    let base = state.backend_base.read().await.clone();
    proxy_http::proxy_http_request(&state.client, &base, req).await
}

pub async fn start_loopback(
    dist_dir: PathBuf,
    backend_base: String,
    client: reqwest::Client,
) -> Result<SocketAddr, String> {
    if !dist_dir.is_dir() {
        return Err(format!(
            "frontend dist not found: {} (run npm run build in frontend/)",
            dist_dir.display()
        ));
    }

    let index = dist_dir.join("index.html");
    if !index.is_file() {
        return Err(format!(
            "index.html missing in {}",
            dist_dir.display()
        ));
    }

    let state = ServerState {
        client,
        backend_base: Arc::new(RwLock::new(backend_base)),
    };

    let static_files = ServeDir::new(&dist_dir).fallback(ServeFile::new(index));

    let app = Router::new()
        .route("/api/{*rest}", any(proxy_api))
        .fallback_service(static_files)
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("127.0.0.1:0")
        .await
        .map_err(|e| e.to_string())?;
    let addr = listener.local_addr().map_err(|e| e.to_string())?;

    tokio::spawn(async move {
        if let Err(err) = axum::serve(listener, app).await {
            tracing::error!("loopback server stopped: {err}");
        }
    });

    Ok(addr)
}
