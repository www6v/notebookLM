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

Release builds start a loopback server that serves `frontend/dist` and proxies `/api` to the URL in settings (default `http://127.0.0.1:8000`).

```bash
cd frontend && npm run build && cd ..
cargo tauri build
```

Bundled macOS/Windows/Linux artifacts appear under `src-tauri/target/release/bundle/`.

**Note:** The loopback server currently resolves `frontend/dist` via the project layout at build time; adjust `dist_dir_for_release` in `src-tauri/src/lib.rs` if you need packaged-app resource paths.

## Settings (IPC + Vue)

In the desktop app, sign in, then open **Settings** (the route requires auth, same as the web app). When the page runs inside the Tauri WebView, an extra card **Desktop app — API server** appears at the top: it calls `settings_get_backend_url` / `settings_set_backend_url` via `@tauri-apps/api`.

Detection uses `window.__TAURI_INTERNALS__` so the card shows in `cargo tauri dev` even without `@tauri-apps/vite-plugin`. Optionally add that plugin if you want `import.meta.env.TAURI_ENV_*` in plain `vite` runs.

- `settings_get_backend_url` — returns stored backend origin
- `settings_set_backend_url` — `{ url: string }` — normalizes and saves; **restart the app** for release builds so the loopback proxy uses the new upstream

Settings file: platform app config directory / `settings.json`.

## WebSocket `/ws`

Vite uses `/ws` for HMR in development only. The FastAPI app does not expose a production `/ws` route today; a WS proxy can be added later if the backend gains one.
