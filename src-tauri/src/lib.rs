mod local_server;
mod proxy_http;
mod public_config;
mod settings;

#[cfg(not(debug_assertions))]
use std::path::PathBuf;
#[cfg(not(debug_assertions))]
use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let mut builder = tauri::Builder::default().plugin(tauri_plugin_opener::init());

    #[cfg(not(debug_assertions))]
    {
        builder = builder.setup(|app| {
            let handle = app.handle();
            let loaded = settings::load(handle)?;
            let bootstrap = settings::normalize_backend_url(&loaded.backend_url)?;
            let backend = tauri::async_runtime::block_on(
                public_config::resolve_upstream_base(
                    &bootstrap,
                    loaded.accept_invalid_certs,
                ),
            );
            let client = proxy_http::build_upstream_client(loaded.accept_invalid_certs)
                .map_err(|e| e.to_string())?;
            let dist = dist_dir_for_release()?;
            let addr = tauri::async_runtime::block_on(local_server::start_loopback(
                dist,
                backend,
                client,
            ))?;
            let url = format!("http://127.0.0.1:{}/", addr.port());
            let parsed: url::Url = url.parse().map_err(|e: url::ParseError| e.to_string())?;
            if let Some(mut w) = handle.get_webview_window("main") {
                w.navigate(parsed).map_err(|e| e.to_string())?;
            }
            Ok(())
        });
    }

    builder
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

/// Release builds load the SPA from disk here (same layout as `frontendDist`).
/// Packaged-app resource paths can be wired later; `cargo tauri build` still
/// bundles assets per `tauri.conf.json`.
#[cfg(not(debug_assertions))]
fn dist_dir_for_release() -> Result<PathBuf, String> {
    let p = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../frontend/dist");
    if p.is_dir() {
        return Ok(p);
    }
    Err(format!(
        "expected dist at {} (run npm run build in frontend/)",
        p.display()
    ))
}
