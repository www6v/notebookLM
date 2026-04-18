# Desktop client design — Tauri 2 (notebookLM)

## 1. Purpose and scope

Deliver a **cross-platform desktop application** (macOS, Windows, Linux) whose **UI and product behavior match the existing Vue 3 + Vuetify web frontend**, while keeping the **Python backend out of the install bundle** (deployment model **A**: shell + user-configured backend).

**In scope**

- Tauri 2 shell hosting the same `frontend` build output as the web app.
- User-configurable backend base URL (scheme + host + port + optional path prefix if ever needed).
- Local loopback HTTP surface for the SPA plus **reverse proxy** for `/api` and `/ws` so the frontend can keep **relative** `baseURL: '/api'` and the same dev-like networking semantics.
- Persistent settings, clear errors when the backend is unreachable, and minimal native affordances (window chrome, optional “open in browser” for external links).

**Out of scope (for this phase)**

- Bundling or auto-installing the Python backend.
- Replacing or duplicating business logic outside the existing Vue app.
- macOS notarization / Windows code signing (document as a follow-up when distribution channels are fixed).

## 2. Technology choice

**Tauri 2** (Rust core + system WebView) is the selected stack.

**Rationale**

- Smaller install footprint and lower idle resource use than an embedded full Chromium stack, while still rendering the existing SPA.
- Strong fit for a **thin shell** that ships static assets and handles OS integration (single instance, deep links later if needed).

**WebView caveat**

- Validate **Vuetify 3**, **TipTap**, **pdfjs**, **KaTeX**, and file-related flows on **Windows (WebView2)**, **macOS (WKWebView)**, and **Linux (WebKitGTK)** during QA; address polyfills or capability flags only if a concrete gap appears.

## 3. High-level architecture

```text
┌─────────────────────────────────────────────────────────┐
│  Tauri main (Rust)                                       │
│  - Read/write user settings (backend URL, TLS options)   │
│  - Start/stop loopback HTTP server (bind 127.0.0.1)      │
│    · GET static files from embedded `frontend/dist`      │
│    · Reverse proxy /api/*  → configured backend          │
│    · Reverse proxy /ws     → configured backend (WS)     │
│  - Open WebView → http://127.0.0.1:<ephemeral>/          │
└─────────────────────────────────────────────────────────┘
          │ HTTP/WS proxy                    │
          ▼                                  │
┌──────────────────────┐            ┌────────┴────────────┐
│  Vue SPA (same dist)  │            │  Existing FastAPI  │
│  axios baseURL /api   │───────────►│  (+ websockets)     │
└──────────────────────┘            └─────────────────────┘
```

**Why loopback + proxy**

- The SPA today uses **relative** API paths (`frontend/src/api/client.ts`, `shareClient.ts`). Serving the app from `http://127.0.0.1:<port>/` and proxying `/api` and `/ws` avoids a large frontend refactor and mirrors the Vite dev proxy behavior (`frontend/vite.config.ts`).
- Browser same-origin rules and cookie behavior stay closer to the web deployment model than `file://` or ad hoc custom schemes for the whole app.

**Ephemeral port**

- Bind to port `0` and read the assigned port to avoid clashes with other local services; persist only the **backend** URL in settings, not the loopback port.

## 4. Components and responsibilities

| Unit | Responsibility |
|------|------------------|
| **Tauri app crate** | Window lifecycle, tray optional later, single-instance policy if desired. |
| **Settings module** | Load/save JSON (or Tauri `store` plugin) under the OS app data directory: backend URL, optional “ignore TLS errors” for private CAs (default off). |
| **Local server module** | Axum (or equivalent) server: static file service for `dist`, `tower_http`/`hyper` reverse proxy for `/api` and WebSocket upgrade for `/ws`. |
| **Commands / events** | IPC from the SPA to Rust for “get/set backend URL”, “restart local server”, “open external URL in system browser”. |
| **Bundled assets** | `frontend/dist` copied or referenced at build time per Tauri `frontendDist` configuration. |
| **Vue frontend** | Ideally **unchanged** for MVP; only add a small **desktop-only** settings surface if product requires in-app configuration (could be a route or dialog calling Tauri IPC). |

## 5. Data flow

1. On startup, Rust loads settings (default: `http://127.0.0.1:8000` or project-documented dev default).
2. Rust starts the loopback server and obtains `(host, port)`.
3. WebView navigates to `http://127.0.0.1:<port>/`.
4. SPA issues `GET/POST … /api/...`; loopback server forwards to `{configured_backend}/api/...` with appropriate `Host`/`X-Forwarded-*` headers if needed for logging.
5. WebSocket clients targeting `/ws` are upgraded and tunneled to the backend WebSocket endpoint.

## 6. Error handling and UX

- If the backend URL is invalid or the proxy cannot connect: show a **lightweight error page** or in-app banner (Rust-served HTML or first-run Tauri window) with “Check server URL” and link to settings — avoid a blank WebView.
- If static assets are missing (misbuild): log in Rust and show a deterministic error screen.
- Timeouts and 502 from proxy should surface as normal HTTP errors to the SPA so existing Axios error handling can apply where possible.

## 7. Security

- **Tauri capabilities**: whitelist only required APIs; no broad `shell:open` without scoping.
- **Content**: Prefer **no** `dangerousRemoteDomainIpcAccess`; the UI origin is loopback only.
- **TLS**: Default strict verification; optional dev-only “trust insecure” must be explicit and labeled in UI.
- **Deep links / file opens**: If added later, validate paths and MIME types before passing to the backend or filesystem.

## 8. Development and release workflow

- **Dev**: `beforeDevCommand` runs Vite; WebView uses dev URL with Vite proxy to backend (fast iteration, same as today). Optional: parity test against loopback server mode.
- **Build**: `beforeBuildCommand` runs `npm run build` in `frontend`; Tauri bundles `dist` into the platform packages.
- **Versioning**: Align desktop semver with the product release policy; document mapping in the implementation plan.

## 9. Testing

- Manual smoke: connect to local FastAPI on `8000`, exercise login/sources/chat flows that hit `/api` and any `/ws` usage.
- Regression matrix: macOS / Windows / Linux for at least startup, settings change, and one full user journey.
- Automated: where feasible, Rust unit tests for URL parsing and proxy path joining; optional integration test with a mock upstream server.

## 10. Success criteria

- User installs the desktop app, points it at a running notebookLM backend, and **sees the same screens and behavior** as the web build for the same backend version.
- No requirement to run Vite or Node on the end user machine in production.
- Changing backend URL does not require rebuilding the SPA.

## 11. Follow-ups (not blocking MVP)

- Code signing and notarization for broad macOS distribution.
- Auto-update channel (Tauri updater) once signing exists.
- Tray icon, global shortcut, and OS file associations if product asks for them.
