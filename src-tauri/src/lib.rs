mod local_server;
mod proxy_http;
mod settings;

#[cfg(not(debug_assertions))]
use std::path::PathBuf;
#[cfg(not(debug_assertions))]
use tauri::Manager;

#[tauri::command]
fn settings_get_backend_url(app: tauri::AppHandle) -> Result<String, String> {
    Ok(settings::load(&app)?.backend_url)
}

#[tauri::command]
fn settings_set_backend_url(app: tauri::AppHandle, url: String) -> Result<(), String> {
    let normalized = settings::normalize_backend_url(&url)?;
    let mut s = settings::load(&app)?;
    s.backend_url = normalized;
    settings::save(&app, &s)?;
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let mut builder = tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            settings_get_backend_url,
            settings_set_backend_url
        ]);

    #[cfg(not(debug_assertions))]
    {
        builder = builder.setup(|app| {
            let handle = app.handle();
            let loaded = settings::load(handle)?;
            let backend = settings::normalize_backend_url(&loaded.backend_url)?;
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
