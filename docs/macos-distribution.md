# macOS：本机能打开、网上下载后提示「身份不明的开发者」

## 原因

1. **隔离属性（quarantine）**  
   通过浏览器（Firefox、Safari 等）下载的 `.dmg` / `.app` 会带上扩展属性 `com.apple.quarantine`。  
   在仓库目录里直接双击 `target/release/bundle/dmg/...` 往往**没有**经过浏览器下载，因此不会触发同一套策略。

2. **Gatekeeper**  
   未使用 **Apple Developer ID** 签名、且未做 **公证（notarization）** 的应用，在带 quarantine 的文件上会被系统拦截，出现「来自身份不明的开发者」类提示。

**结论**：这不是应用逻辑错误，而是 **macOS 对未签名/未公证分发包的正常行为**。要对外公开发 DMG，需要走下面的「正式分发」流程。

---

## 正式解决（对外分发必做）

需要 **Apple Developer Program**（付费账号）与在 **Mac** 上执行构建（或具备相应证书的 CI）。

1. **Developer ID Application** 证书  
   在 [Certificates, IDs & Profiles](https://developer.apple.com/account/resources/certificates/list) 创建并安装到本机钥匙串。

2. **构建时签名**  
   在运行 `cargo tauri build` 的机器上执行：

   ```bash
   security find-identity -v -p codesigning
   ```

   将输出的 **Developer ID Application: …** 整行设为环境变量（或在 `tauri.conf.json` 的 `bundle.macOS.signingIdentity` 中填写，不推荐把身份写死进仓库）：

   ```bash
   export APPLE_SIGNING_IDENTITY="Developer ID Application: Your Name (TEAMID)"
   ```

3. **公证（Notarization）**  
   仅签名仍可能拦下载；需让 Apple 公证。常用方式（二选一）：

   - **App Store Connect API 密钥**（适合 CI）：设置 `APPLE_API_KEY`、`APPLE_API_ISSUER`、`APPLE_API_KEY_PATH`（或按 [Tauri 环境变量说明](https://v2.tauri.app/reference/environment-variables/) 配置）。
   - **Apple ID + 应用专用密码**：`APPLE_ID`、`APPLE_PASSWORD` 等（见官方文档）。

4. **参考文档**  
   - [Tauri：macOS 代码签名](https://v2.tauri.app/distribute/sign/macos/)  
   - 本仓库已在 `src-tauri/tauri.conf.json` 中启用 `entitlements.plist` 与 **hardened runtime**，便于你在具备证书后直接出可分发包。

---

## 临时方案（仅内测 / 自用，不替代签名公证）

**不要**作为对终端用户的产品方案；仅方便开发/内测。

1. **首次仍要打开**：在 Finder 中对 **App**（或 DMG 内的 App）**右键 → 打开**，在二次确认里选择「打开」。  
2. **系统设置**：**隐私与安全性** 中若出现「仍要打开」，可点按允许（因 macOS 版本而异）。  
3. **去掉隔离属性**（确认来源可信后再用）：

   ```bash
   xattr -dr com.apple.quarantine /path/to/NotebookLM.app
   ```

   或对挂载的 DMG 内的 `.app` 执行同样命令。

---

## 与本项目配置的对应关系

| 项目 | 说明 |
|------|------|
| `bundle.identifier` | `com.notebooklm.desktop`，与 Apple 上 **Bundle ID** 一致时便于公证。 |
| `src-tauri/entitlements.plist` | WebView / JIT 所需权利，公证前签名会使用。 |
| `bundle.macOS.hardenedRuntime` | 已设为 `true`，与公证要求一致。 |

完成签名与公证后，重新打 DMG 再经浏览器下载验证，应不再出现「身份不明的开发者」拦截（在 Apple 策略未变更的前提下）。
