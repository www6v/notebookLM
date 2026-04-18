//! Persisted connection settings for the desktop shell.

use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};
use tauri::Manager;
use url::Url;

const DEFAULT_BACKEND: &str = "http://127.0.0.1:8000";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct AppSettings {
    /// Origin of the FastAPI server (no trailing slash).
    pub backend_url: String,
    #[serde(default)]
    pub accept_invalid_certs: bool,
}

impl Default for AppSettings {
    fn default() -> Self {
        Self {
            backend_url: DEFAULT_BACKEND.to_string(),
            accept_invalid_certs: false,
        }
    }
}

/// Normalize user input: trim, validate scheme/host, strip trailing slash only.
pub fn normalize_backend_url(input: &str) -> Result<String, String> {
    let t = input.trim();
    if t.is_empty() {
        return Err("backend URL is empty".into());
    }
    let u = Url::parse(t).map_err(|e| format!("invalid URL: {e}"))?;
    u.host_str()
        .ok_or_else(|| "URL must include host".to_string())?;
    if u.scheme() != "http" && u.scheme() != "https" {
        return Err("only http and https URLs are allowed".into());
    }
    Ok(t.trim_end_matches('/').to_string())
}

pub fn settings_path(app: &tauri::AppHandle) -> Result<PathBuf, String> {
    let dir = app
        .path()
        .app_config_dir()
        .map_err(|e| e.to_string())?;
    fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
    Ok(dir.join("settings.json"))
}

pub fn load(app: &tauri::AppHandle) -> Result<AppSettings, String> {
    let p = settings_path(app)?;
    if !p.exists() {
        return Ok(AppSettings::default());
    }
    let raw = fs::read_to_string(&p).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn save(app: &tauri::AppHandle, s: &AppSettings) -> Result<(), String> {
    let p = settings_path(app)?;
    let raw = serde_json::to_string_pretty(s).map_err(|e| e.to_string())?;
    fs::write(&p, raw).map_err(|e| e.to_string())
}

pub fn load_from_path(path: &Path) -> Result<AppSettings, String> {
    if !path.exists() {
        return Ok(AppSettings::default());
    }
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn save_to_path(path: &Path, s: &AppSettings) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let raw = serde_json::to_string_pretty(s).map_err(|e| e.to_string())?;
    fs::write(path, raw).map_err(|e| e.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn normalize_strips_trailing_slash() {
        assert_eq!(
            normalize_backend_url("http://127.0.0.1:8000/").unwrap(),
            "http://127.0.0.1:8000"
        );
    }

    #[test]
    fn normalize_rejects_empty() {
        assert!(normalize_backend_url("   ").is_err());
    }

    #[test]
    fn normalize_accepts_https() {
        assert_eq!(
            normalize_backend_url("https://api.example.com").unwrap(),
            "https://api.example.com"
        );
    }

    #[test]
    fn roundtrip_save_load() {
        let dir = std::env::temp_dir().join("notebooklm-settings-test");
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(&dir).unwrap();
        let path = dir.join("settings.json");
        let s = AppSettings {
            backend_url: "https://example.com".to_string(),
            accept_invalid_certs: true,
        };
        save_to_path(&path, &s).unwrap();
        let loaded = load_from_path(&path).unwrap();
        assert_eq!(loaded, s);
    }

    #[test]
    fn load_missing_file_returns_default() {
        let p = std::env::temp_dir().join("notebooklm-settings-missing-xyz.json");
        let _ = fs::remove_file(&p);
        let loaded = load_from_path(&p).unwrap();
        assert_eq!(loaded, AppSettings::default());
    }
}
