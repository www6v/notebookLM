#!/usr/bin/env node

const fs = require('fs');
const os = require('os');
const path = require('path');

const DEFAULT_BASE_URL = 'http://localhost:8000';
const DEFAULT_LAST_CHECK_FILE = path.join(
  os.homedir(),
  '.config/notebooklm/last_update_check'
);

const ERR_PROGRAMMATIC = -100;
const ERR_UPDATE_AVAILABLE = -200;

function readFileSafe(filePath) {
  try {
    return fs.readFileSync(filePath, 'utf8').trim();
  } catch {
    return '';
  }
}

function ensureDir(filePath) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
}

function loadCredentials(options = {}) {
  const clientId =
    options.clientId ||
    process.env.NOTEBOOKLM_OPENAPI_CLIENTID ||
    process.env.NOTEBOOKLM_CLIENT_ID ||
    readFileSafe(path.join(os.homedir(), '.config/notebooklm/client_id'));
  const apiKey =
    options.apiKey ||
    process.env.NOTEBOOKLM_OPENAPI_APIKEY ||
    process.env.NOTEBOOKLM_API_KEY ||
    readFileSafe(path.join(os.homedir(), '.config/notebooklm/api_key'));

  if (!clientId || !apiKey) {
    const err = new Error('missing credentials');
    err.code = ERR_PROGRAMMATIC;
    err.msg =
      '未找到 NotebookLM 凭证（clientId / apiKey）。请设置 NOTEBOOKLM_OPENAPI_CLIENTID 和 NOTEBOOKLM_OPENAPI_APIKEY，或将凭证放置在 ~/.config/notebooklm/ 目录下。';
    throw err;
  }

  return { clientId, apiKey };
}

function loadSkillVersion(options = {}) {
  if (options.skillVersion) return options.skillVersion;
  if (process.env.NOTEBOOKLM_SKILL_VERSION) {
    return process.env.NOTEBOOKLM_SKILL_VERSION;
  }

  const metaPath = path.join(__dirname, 'meta.json');
  try {
    const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
    return meta.version || 'unknown';
  } catch {
    return 'unknown';
  }
}

async function postJson(apiPath, body, requestOptions) {
  const { clientId, apiKey, skillVersion, baseUrl } = requestOptions;
  const url = `${baseUrl.replace(/\/$/, '')}/${apiPath.replace(/^\//, '')}`;

  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'notebooklm-openapi-clientid': clientId,
      'notebooklm-openapi-apikey': apiKey,
      'notebooklm-openapi-ctx': `skill_version=${skillVersion}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  const text = await res.text();
  if (!res.ok) {
    let parsed = {};
    try {
      parsed = JSON.parse(text || '{}');
    } catch {
      parsed = {};
    }
    const err = new Error(parsed.msg || text || res.statusText);
    err.code = ERR_PROGRAMMATIC;
    err.msg = parsed.msg || `HTTP ${res.status}: ${text}`;
    throw err;
  }
  return text;
}

function readToday() {
  return new Date().toISOString().slice(0, 10);
}

function saveTodayChecked(lastCheckFile, today) {
  ensureDir(lastCheckFile);
  fs.writeFileSync(lastCheckFile, today, 'utf8');
}

async function checkSkillUpdateIfNeeded(requestOptions) {
  const { forceCheck, skillVersion, lastCheckFile } = requestOptions;
  const today = readToday();
  const checkedDay = readFileSafe(lastCheckFile);

  if (!forceCheck && checkedDay === today) {
    return;
  }

  let updateResponseText;
  try {
    updateResponseText = await postJson(
      'openapi/notebook/v1/check_skill_update',
      { version: skillVersion },
      requestOptions
    );
  } catch {
    return;
  }

  saveTodayChecked(lastCheckFile, today);

  let updateResp;
  try {
    updateResp = JSON.parse(updateResponseText || '{}');
  } catch {
    updateResp = {};
  }

  const data = updateResp.data || {};
  const latestVersion = data.latest_version || '';
  const releaseDesc = data.release_desc || '';
  const instruction = data.instruction || '';
  if (latestVersion && latestVersion !== skillVersion && instruction) {
    const updateContext = {
      current_version: skillVersion,
      latest_version: latestVersion,
      release_desc: releaseDesc,
      instruction,
      checked_at: new Date().toISOString(),
    };

    process.stdout.write(JSON.stringify(updateContext));

    const err = new Error('update available');
    err.code = ERR_UPDATE_AVAILABLE;
    err.msg = `发现新版本 skill：${latestVersion}（当前：${skillVersion}）。${instruction}`;
    err.updateContext = updateContext;
    throw err;
  }
}

async function notebooklmApi(apiPath, body, options = {}) {
  const forceCheck =
    options.forceCheck ||
    options.forceUpdateCheck ||
    process.env.NOTEBOOKLM_FORCE_UPDATE_CHECK === '1';
  const baseUrl =
    options.baseUrl || process.env.NOTEBOOKLM_BASE_URL || DEFAULT_BASE_URL;
  const lastCheckFile =
    options.lastCheckFile ||
    process.env.NOTEBOOKLM_LAST_CHECK_FILE ||
    DEFAULT_LAST_CHECK_FILE;
  const { clientId, apiKey } = loadCredentials(options);
  const skillVersion = loadSkillVersion(options);

  const requestOptions = {
    forceCheck,
    clientId,
    apiKey,
    skillVersion,
    baseUrl,
    lastCheckFile,
  };

  if (!apiPath.includes('check_skill_update')) {
    await checkSkillUpdateIfNeeded(requestOptions);
  }

  return postJson(apiPath, body, requestOptions);
}

function parseBody(raw) {
  if (!raw || !raw.trim()) return {};

  try {
    return JSON.parse(raw);
  } catch {
    const err = new Error('invalid JSON body');
    err.code = ERR_PROGRAMMATIC;
    err.msg = '请求 body 不是合法的 JSON。';
    throw err;
  }
}

function parseOptions(raw, restArgs) {
  let options = {};

  if (raw && raw.trim()) {
    try {
      options = JSON.parse(raw);
    } catch {
      const err = new Error('invalid options JSON');
      err.code = ERR_PROGRAMMATIC;
      err.msg = 'options 参数不是合法的 JSON。';
      throw err;
    }
  }

  if (restArgs.includes('--force-update-check')) {
    options.forceCheck = true;
  }

  return options;
}

async function main() {
  const [, , apiPath, rawBody = '{}', rawOptions = '{}', ...rest] = process.argv;

  if (!apiPath) {
    process.stderr.write(
      JSON.stringify({ code: ERR_PROGRAMMATIC, msg: '缺少必需参数：apiPath。' })
    );
    process.exit(1);
  }

  try {
    const body = parseBody(rawBody);
    const options = parseOptions(rawOptions, rest);
    const resp = await notebooklmApi(apiPath, body, options);
    process.stdout.write(resp);
  } catch (err) {
    const code = err && typeof err.code === 'number' ? err.code : ERR_PROGRAMMATIC;
    const msg = (err && err.msg) || (err && err.message) || '未知错误';
    process.stderr.write(JSON.stringify({ code, msg }));
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = {
  notebooklmApi,
  ERR_PROGRAMMATIC,
  ERR_UPDATE_AVAILABLE,
};
