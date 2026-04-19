# NotebookLM desktop (Tauri 2)

## Prerequisites

- [Rust](https://www.rust-lang.org/tools/install) (stable) and Cargo
- Node.js (for the Vue frontend)
- System packages per [Tauri prerequisites](https://v2.tauri.app/start/prerequisites/)

## Development

From the repository root:

```bash
cd frontend && npm install && cd ..
cargo tauri dev
```

This starts Vite on `http://localhost:5173` (with `/api` proxied to the backend per `frontend/vite.config.ts`) and opens the desktop window.

## Release-style run (loopback + `dist`)

Release builds start a loopback server that serves `frontend/dist` and proxies `/api` to the **effective** upstream: server `desktop_backend_url` from `GET /api/public/client-config` when set, otherwise the bootstrap URL in local `settings.json` (default `http://127.0.0.1:8000`).

```bash
cd frontend && npm run build && cd ..
cargo tauri build
```

Bundled macOS/Windows/Linux artifacts appear under `src-tauri/target/release/bundle/`.

**macOS:** If the DMG works locally but fails after download with Gatekeeper / 「身份不明的开发者」, see [macOS distribution & Gatekeeper](macos-distribution.md) (code signing + notarization).

**Note:** The loopback server currently resolves `frontend/dist` via the project layout at build time; adjust `dist_dir_for_release` in `src-tauri/src/lib.rs` if you need packaged-app resource paths.

## Admin: fleet-wide desktop API URL

Sign in as **admin**, open **Admin** → **Desktop API** (or `/:locale/admin/desktop`). The UI uses **`GET /api/public/client-config`** and **`PUT /api/admin/client-config`** (HTTP, same as a browser).

- **Server:** `desktop_backend_url` is stored in **`system_settings`** (shared DB).
- **Desktop (release):** On startup, the shell requests `{bootstrap}/api/public/client-config` where **bootstrap** is `backend_url` in local `settings.json` (default `http://127.0.0.1:8000`). If the JSON includes a non-empty `desktop_backend_url`, that value becomes the reverse-proxy upstream. **Restart** each desktop app after a change.

Tauri detection in the Vue app uses `window.__TAURI_INTERNALS__` so the admin entry appears in `cargo tauri dev` without `@tauri-apps/vite-plugin`.

**Bootstrap file:** App config directory / `settings.json` — only affects where to fetch `client-config`, not the fleet URL itself.

## WebSocket `/ws`

Vite uses `/ws` for HMR in development only. The FastAPI app does not expose a production `/ws` route today; a WS proxy can be added later if the backend gains one.
