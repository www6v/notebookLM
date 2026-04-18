# Tauri 2 desktop client implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a Tauri 2 desktop shell that serves the existing Vue `frontend/dist` over loopback, reverse-proxies `/api` (including streaming bodies) and `/ws` to a user-configured backend URL, and matches the approved spec in `docs/superpowers/specs/2026-04-18-desktop-client-tauri-design.md`.

**Architecture:** Rust owns settings and an Axum server bound to `127.0.0.1:0`; the WebView loads `http://127.0.0.1:<port>/`. API traffic stays relative (`/api/...`) in the SPA; the Axum layer forwards to `{backend}{path}`. Development uses `devUrl` + Vite proxy unchanged; production uses bundled `frontend/dist` plus the loopback server.

**Tech stack:** Tauri 2, Rust 1.77+, Axum 0.8, `tower-http` (static + trace), `reqwest` (HTTP/1.1 proxy with streaming), `tokio-tungstenite` + Axum `ws` for WebSocket tunneling (if backend exposes `/ws`; confirm routes in `backend/` during Task 6), Serde JSON settings on disk, `@tauri-apps/api` in Vue for desktop-only settings.

**Spec source:** `docs/superpowers/specs/2026-04-18-desktop-client-tauri-design.md`

---

## File map (new vs touched)

| Path | Role |
|------|------|
| `src-tauri/Cargo.toml` | Crate deps, binary name, Tauri features. |
| `src-tauri/tauri.conf.json` | `build.frontendDist`, `devUrl`, before-dev/build commands, bundle identifiers. |
| `src-tauri/capabilities/default.json` | Minimal allowlist (`core:webview`, `core:window`, `shell:open` scoped if used). |
| `src-tauri/src/lib.rs` | `run()` entry: state, spawn Axum, navigate WebView. |
| `src-tauri/src/settings.rs` | Load/save JSON; URL normalization; unit tests. |
| `src-tauri/src/local_server.rs` | Axum router: `ServeDir`, `/api/*` proxy, `/ws` upgrade. |
| `src-tauri/src/proxy_http.rs` | `reqwest` forwarder preserving method, query, hop-by-hop header filtering, streaming response. |
| `src-tauri/src/proxy_ws.rs` | Optional WebSocket bidirectional copy (only if `/ws` is confirmed in use). |
| `frontend/package.json` | Add `@tauri-apps/api` devDependency; add `tauri` script aliases if desired. |
| `frontend/src/...` | Desktop settings UI + `invoke` for get/set backend + restart server (minimal new route or dialog). |
| `README.md` or `docs/desktop.md` | How to run `cargo tauri dev` / build; default backend URL. |

---

### Task 1: Prerequisites and CLI

**Files:** none (environment).

- [ ] **Step 1: Install Rust toolchain**

Run: `rustc --version`  
Expected: `rustc 1.77.0` or newer (adjust project MSRV in `Cargo.toml` if team pins lower).

- [ ] **Step 2: Install Tauri 2 CLI**

Run: `cargo install tauri-cli --locked`  
Expected: `cargo tauri --version` prints a `2.x` CLI.

- [ ] **Step 3: Commit (empty if no files)**

Skip commit if nothing changed; otherwise document versions in `docs/desktop.md` when that file is added in Task 9.

---

### Task 2: Initialize Tauri in repo root

**Files:**

- Create: `src-tauri/Cargo.toml`, `src-tauri/tauri.conf.json`, `src-tauri/build.rs`, `src-tauri/src/main.rs`, `src-tauri/src/lib.rs`, `src-tauri/capabilities/default.json`, `src-tauri/.gitignore` (as generated)

- [ ] **Step 1: Run non-interactive init from repository root**

Run (single line; paths relative to `src-tauri` per Tauri docs):

```bash
cd /Users/t-wangwei07/Downloads/workspacePy/mycode/notebookLM
cargo tauri init --ci \
  --app-name notebooklm-desktop \
  --window-title "NotebookLM" \
  --frontend-dist ../frontend/dist \
  --dev-url http://localhost:5173 \
  --before-dev-command "sh -c 'cd ../frontend && npm run dev'" \
  --before-build-command "sh -c 'cd ../frontend && npm run build'"
```

Expected: `src-tauri/` exists and `cargo tauri dev` can start (may fail until frontend runs; that is OK).

If a future CLI adds `--before-dev-command-path`, you may switch to that form for clearer logs; the `sh -c` form is the portable default.

- [ ] **Step 2: Verify `tauri.conf.json`**

Open `src-tauri/tauri.conf.json` and confirm `build.devUrl` is `http://localhost:5173`, `build.frontendDist` is `../frontend/dist`, and `identifier` uses a reverse-DNS string you own (example: `com.yourorg.notebooklm`).

- [ ] **Step 3: Commit**

```bash
git add src-tauri
git commit -m "chore: scaffold Tauri 2 desktop shell"
```

---

### Task 3: Settings module (TDD)

**Files:**

- Create: `src-tauri/src/settings.rs`
- Modify: `src-tauri/src/lib.rs` (add `mod settings;` and re-export as needed)

- [ ] **Step 1: Add failing unit tests in `settings.rs`**

Create `src-tauri/src/settings.rs` with:

```rust
//! User-editable backend connection settings.

use serde::{Deserialize, Serialize};
use std::path::PathBuf;
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
/// Path prefixes (e.g. `https://host/app`) are preserved if you later need them;
/// document product rules if only origin-style URLs are allowed.
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
}
```

- [ ] **Step 2: Add dependencies in `src-tauri/Cargo.toml`**

Under `[dependencies]` add:

```toml
serde = { version = "1", features = ["derive"] }
serde_json = "1"
url = "2"
```

- [ ] **Step 3: Run tests (expect PASS after code compiles)**

Run:

```bash
cd /Users/t-wangwei07/Downloads/workspacePy/mycode/notebookLM/src-tauri
cargo test normalize_
```

Expected: three tests pass.

- [ ] **Step 4: Implement `settings_file_path` and load/save (same file)**

Append to `settings.rs`:

```rust
use std::fs;
use tauri::Manager;

/// Requires `tauri` crate feature `path` in `Cargo.toml`.
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
```

Add test doubles are not required for `tauri::AppHandle` in unit tests; integration can be manual.

- [ ] **Step 5: Commit**

```bash
git add src-tauri/Cargo.toml src-tauri/src/settings.rs src-tauri/src/lib.rs
git commit -m "feat(desktop): add persisted settings and URL normalization"
```

---

### Task 4: HTTP reverse proxy with streaming (Axum + reqwest)

**Files:**

- Create: `src-tauri/src/proxy_http.rs`
- Modify: `src-tauri/Cargo.toml`, `src-tauri/src/local_server.rs` (router wiring in Task 5)

- [ ] **Step 1: Add crates**

In `src-tauri/Cargo.toml`:

```toml
axum = { version = "0.8", features = ["macros", "ws"] }
tokio = { version = "1", features = ["full"] }
reqwest = { version = "0.12", default-features = false, features = ["json", "stream", "rustls-tls"] }
tower-http = { version = "0.6", features = ["fs", "trace"] }
http = "1"
futures-util = "0.3"
tracing = "0.1"
```

- [ ] **Step 2: Implement streaming forward helper**

Create `src-tauri/src/proxy_http.rs`:

```rust
use axum::{
    body::Body,
    extract::Request,
    response::{IntoResponse, Response},
};
use futures_util::StreamExt;
use http::header::{CONNECTION, HOST, TRANSFER_ENCODING, UPGRADE};
use reqwest::Client;

fn hop_by_hop_headers() -> &'static [http::HeaderName] {
    use http::header::{
        CONNECTION, PROXY_AUTHENTICATE, PROXY_AUTHORIZATION, TE, TRAILER,
        TRANSFER_ENCODING, UPGRADE,
    };
    &[
        CONNECTION,
        TRANSFER_ENCODING,
        UPGRADE,
        PROXY_AUTHENTICATE,
        PROXY_AUTHORIZATION,
        TE,
        TRAILER,
        HOST,
    ]
}

pub fn build_upstream_client(accept_invalid_certs: bool) -> Result<Client, reqwest::Error> {
    let mut b = Client::builder().use_rustls_tls();
    if accept_invalid_certs {
        b = b.danger_accept_invalid_certs(true);
    }
    b.build()
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
        if hop_by_hop_headers().contains(&k) {
            continue;
        }
        rb = rb.header(k.as_str(), v.as_bytes());
    }
    let body_bytes = match axum::body::to_bytes(req.into_body(), usize::MAX).await {
        Ok(b) => b,
        Err(e) => {
            return (
                http::StatusCode::BAD_GATEWAY,
                format!("read body: {e}"),
            )
                .into_response();
        }
    };
    rb = rb.body(body_bytes);

    let upstream = match rb.send().await {
        Ok(r) => r,
        Err(e) => {
            return (
                http::StatusCode::BAD_GATEWAY,
                format!("upstream: {e}"),
            )
                .into_response();
        }
    };

    let mut res = Response::builder().status(upstream.status());
    for (k, v) in upstream.headers().iter() {
        if hop_by_hop_headers().contains(&k) {
            continue;
        }
        if k == TRANSFER_ENCODING || k == CONNECTION || k == UPGRADE {
            continue;
        }
        res = res.header(k, v);
    }
    let stream = upstream.bytes_stream().map(|chunk| {
        chunk.map_err(|_| std::io::Error::new(std::io::ErrorKind::Other, "upstream stream"))
    });
    let body = Body::from_stream(stream);
    res.body(body).unwrap()
}
```

- [ ] **Step 3: Manual check**

With a dummy backend or `python -m http.server`, temporarily wire a route in a throwaway binary or in Task 5 and `curl -N` an SSE endpoint to confirm chunks flow (no full automation required in MVP).

- [ ] **Step 4: Commit**

```bash
git add src-tauri/src/proxy_http.rs src-tauri/Cargo.toml
git commit -m "feat(desktop): add streaming HTTP proxy helper"
```

---

### Task 5: Loopback Axum server + static `dist`

**Files:**

- Create: `src-tauri/src/local_server.rs`
- Modify: `src-tauri/src/lib.rs`

- [ ] **Step 1: Implement server start**

`local_server.rs` should:

1. Resolve absolute path to `frontend/dist` at runtime (Tauri resource path or `CARGO_MANIFEST_DIR`-relative in dev; use `tauri::api::path::resource_dir` in release per Tauri 2 resource bundling docs).
2. `TcpListener::bind("127.0.0.1:0").await` and read local address port.
3. Build Axum: `ServeDir::new(dist_path)` for `GET /*` fallback `index.html` for SPA (use `ServeDir::fallback` or `fallback_service` routing order).
4. Nest `/api` routes to call `proxy_http::proxy_http_request` with `State` holding `Client` and `backend_base: Arc<RwLock<String>>` or `Arc<AppConfig>`.

Example router sketch (complete in implementation):

```rust
use std::sync::Arc;
use tokio::sync::RwLock;

#[derive(Clone)]
pub struct ProxyState {
    pub client: reqwest::Client,
    pub backend_base: Arc<RwLock<String>>,
}

async fn api_fallback(
    axum::extract::State(state): axum::extract::State<ProxyState>,
    req: Request<Body>,
) -> impl IntoResponse {
    let base = state.backend_base.read().await.clone();
    proxy_http::proxy_http_request(&state.client, &base, req).await
}
```

- [ ] **Step 2: Spawn server on Tokio and return `SocketAddr`**

Expose `pub async fn start(...) -> Result<SocketAddr, String>` used from `lib.rs` before WebView navigation.

- [ ] **Step 3: Commit**

```bash
git add src-tauri/src/local_server.rs src-tauri/src/lib.rs
git commit -m "feat(desktop): loopback static server and API proxy"
```

---

### Task 6: WebSocket `/ws` (conditional on backend)

**Files:**

- Create: `src-tauri/src/proxy_ws.rs` (if needed)
- Modify: `src-tauri/src/local_server.rs`

- [ ] **Step 1: Confirm backend routes**

Run: `rg -n "websocket|WebSocketRoute|/ws" /Users/t-wangwei07/Downloads/workspacePy/mycode/notebookLM/backend`  
If the app does not expose `/ws` to the SPA in production, document “Vite HMR only” and **skip** WebSocket proxy for MVP; keep Vite `devUrl` for dev.

- [ ] **Step 2: If `/ws` is required, implement Axum `ws` handler**

Upgrade client WebSocket to `tokio_tungstenite::connect_async(backend_ws_url)` and spawn two `copy_bidirectional` tasks; strip hop-by-hop headers. Use `ws` or `wss` derived from `backend_url` + path `/ws`.

- [ ] **Step 3: Commit**

```bash
git add src-tauri/src/proxy_ws.rs src-tauri/src/local_server.rs
git commit -m "feat(desktop): proxy WebSocket /ws to backend"
```

---

### Task 7: Tauri lifecycle — production vs dev

**Files:**

- Modify: `src-tauri/src/lib.rs`, `src-tauri/tauri.conf.json`

- [ ] **Step 1: In `setup` hook**

Pseudo-flow (implement concretely):

```rust
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            let handle = app.handle().clone();
            let settings = settings::load(&handle)?;
            let backend = settings::normalize_backend_url(&settings.backend_url)?;
            let client = proxy_http::build_upstream_client(settings.accept_invalid_certs)?;
            // spawn local_server::start, store JoinHandle + ProxyState in .manage()
            // main_window.navigate(format!("http://127.0.0.1:{port}/"))
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_backend_url,
            set_backend_url,
            restart_local_server
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

In **development**, prefer loading `devUrl` only (Tauri default) and skip loopback **or** optionally use loopback for parity; pick one behavior and document it in `docs/desktop.md` to avoid double-proxy confusion.

Recommended: **`tauri dev` → WebView uses `http://localhost:5173` only** (Vite proxies `/api`). **`tauri build` → loopback + `dist`**.

- [ ] **Step 2: Error page**

If `frontend/dist` missing in release build, show `tauri::WebviewWindow` with simple HTML string or a second minimal window explaining “run `npm run build` in frontend”.

- [ ] **Step 3: Commit**

```bash
git add src-tauri/src/lib.rs src-tauri/tauri.conf.json
git commit -m "feat(desktop): wire startup, dev vs release modes"
```

---

### Task 8: IPC commands + Vue settings surface

**Files:**

- Modify: `frontend/package.json`, new Vue component and route (exact paths follow existing router layout under `frontend/src/router/` and `frontend/src/views/`)

- [ ] **Step 1: Add dependency**

Run:

```bash
cd /Users/t-wangwei07/Downloads/workspacePy/mycode/notebookLM/frontend
npm install @tauri-apps/api@^2
```

Expected: `package.json` and `package-lock.json` updated.

- [ ] **Step 2: Rust commands**

In `lib.rs`, implement:

```rust
#[tauri::command]
fn get_backend_url(app: tauri::AppHandle) -> Result<String, String> {
    let s = settings::load(&app)?;
    Ok(s.backend_url)
}

#[tauri::command]
fn set_backend_url(app: tauri::AppHandle, url: String) -> Result<(), String> {
    let normalized = settings::normalize_backend_url(&url)?;
    let mut s = settings::load(&app)?;
    s.backend_url = normalized;
    settings::save(&app, &s)?;
    Ok(())
}

#[tauri::command]
async fn restart_local_server(/* state */) -> Result<u16, String> {
    // restart Axum listener, update managed port, return new port
    Ok(0)
}
```

Wire real restart logic to match `ProxyState` from Task 5.

- [ ] **Step 3: Vue desktop settings page**

Use `import { invoke } from '@tauri-apps/api/core'` guarded by `if (import.meta.env.TAURI_ENV_PLATFORM)` or feature flag so web build does not bundle failures. Example save handler:

```typescript
import { invoke } from '@tauri-apps/api/core'

const saveBackend = async (url: string) => {
  await invoke('set_backend_url', { url })
  await invoke('restart_local_server')
}
```

Add a link from existing app settings menu when `window.__TAURI_INTERNALS__` exists (or use `import.meta.env.TAURI_PLATFORM` per Tauri 2 docs).

- [ ] **Step 4: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src src-tauri/src/lib.rs
git commit -m "feat(desktop): IPC and Vue backend URL settings"
```

---

### Task 9: Documentation and CI notes

**Files:**

- Create: `docs/desktop.md`

- [ ] **Step 1: Write `docs/desktop.md`**

Include:

- `cargo tauri dev` prerequisites (Node, Rust).
- Default backend `http://127.0.0.1:8000`.
- Remote container usage: set backend to `https://...` and ensure ingress supports WebSocket if enabled.
- `cargo tauri build` artifact locations under `src-tauri/target/release/bundle/`.

- [ ] **Step 2: Optional CI job snippet**

Document a GitHub Actions job matrix `macos-latest`, `windows-latest`, `ubuntu-latest` calling `cargo tauri build` with `frontend` build cached; do not add workflow file unless requested.

- [ ] **Step 3: Commit**

```bash
git add docs/desktop.md
git commit -m "docs: add desktop client runbook"
```

---

### Task 10: Verification matrix (manual)

**Files:** none.

- [ ] **Step 1: Local backend smoke**

Run backend on `8000`, desktop pointed at default URL; verify login, sources list, chat non-stream and **chat stream** (`/api/chat/.../messages/stream`).

- [ ] **Step 2: Remote HTTPS**

Point backend URL to staging HTTPS; verify TLS; toggle `accept_invalid_certs` only on a known-bad cert host in a test environment.

- [ ] **Step 3: Platforms**

Repeat smoke on macOS, Windows, Linux per spec §9.

- [ ] **Step 4: Commit**

Only if fixing issues found; otherwise no commit.

---

## Spec self-review (plan vs spec)

| Spec section | Plan coverage |
|--------------|---------------|
| §1 Tauri shell + same dist | Tasks 2, 5, 7 |
| §1 User-configurable backend | Tasks 3, 8 |
| §1 Loopback + `/api` `/ws` proxy | Tasks 4–6 |
| §1 Persistent settings | Task 3 |
| §1 Errors / missing dist | Task 7 |
| §2 WebView caveat / QA | Task 10 |
| §3 Ephemeral port | Task 5 |
| §6 Error handling / 502 | `proxy_http` returns 502-style responses |
| §7 Security capabilities | Task 2 follow-up: tighten `capabilities/default.json` |
| §8 Dev vs release | Task 7 |
| §9 Testing | Tasks 3 (unit), 10 (manual) |
| §10 Success criteria | Task 10 |
| §11 Follow-ups | Out of plan scope |

**Placeholder scan:** None intentional; Task 6 branches on confirmed `/ws` usage.

**Type consistency:** `AppSettings.backend_url` string matches `normalize_backend_url` output; `ProxyState` uses same string form as `reqwest` URL prefix.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-18-desktop-tauri-implementation.md`. Two execution options:

**1. Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach do you prefer?
