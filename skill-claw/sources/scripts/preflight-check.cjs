#!/usr/bin/env node
'use strict';

/**
 * Preflight check for uploading a file to NotebookLM via OpenAPI + COS.
 * Aligned with backend ALLOWED_EXTENSIONS / FILE_TYPE_MAP.
 */

const fs = require('node:fs');
const path = require('node:path');

const EXT_MAP = {
  pdf: { source_type: 'pdf', content_type: 'application/pdf' },
  doc: { source_type: 'docx', content_type: 'application/msword' },
  docx: { source_type: 'docx', content_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' },
  txt: { source_type: 'txt', content_type: 'text/plain' },
  md: { source_type: 'markdown', content_type: 'text/markdown' },
  csv: { source_type: 'csv', content_type: 'text/csv' },
  pptx: { source_type: 'pptx', content_type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation' },
  bmp: { source_type: 'image', content_type: 'image/bmp' },
  gif: { source_type: 'image', content_type: 'image/gif' },
  png: { source_type: 'image', content_type: 'image/png' },
  webp: { source_type: 'image', content_type: 'image/webp' },
  jpeg: { source_type: 'image', content_type: 'image/jpeg' },
  jpg: { source_type: 'image', content_type: 'image/jpeg' },
  ico: { source_type: 'image', content_type: 'image/x-icon' },
  mp3: { source_type: 'audio', content_type: 'audio/mpeg' },
  wav: { source_type: 'audio', content_type: 'audio/wav' },
  m4a: { source_type: 'audio', content_type: 'audio/x-m4a' },
  aac: { source_type: 'audio', content_type: 'audio/aac' },
  ogg: { source_type: 'audio', content_type: 'audio/ogg' },
  opus: { source_type: 'audio', content_type: 'audio/opus' },
  avi: { source_type: 'video', content_type: 'video/x-msvideo' },
  mp4: { source_type: 'video', content_type: 'video/mp4' },
  mpeg: { source_type: 'video', content_type: 'video/mpeg' },
};

const MB = 1024 * 1024;
const DEFAULT_SIZE_LIMIT = 200 * MB;

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i++) {
    if (argv[i].startsWith('--') && i + 1 < argv.length) {
      args[argv[i].replace(/^--/, '')] = argv[i + 1];
      i += 1;
    }
  }
  return args;
}

function fail(result) {
  console.log(JSON.stringify({ pass: false, ...result }));
  process.exit(1);
}

const args = parseArgs(process.argv);
if (!args.file) {
  console.error('Usage: node preflight-check.cjs --file <path> [--content-type <mime>]');
  process.exit(2);
}

const filePath = path.resolve(args.file);
const fileName = path.basename(filePath);
const extMatch = fileName.match(/\.([^.]+)$/);
const ext = extMatch ? extMatch[1].toLowerCase() : '';
const inputContentType = args['content-type'] || '';
const base = { file_path: filePath, file_name: fileName, file_ext: ext };

let stat;
try {
  stat = fs.statSync(filePath);
} catch (err) {
  if (err.code === 'ENOENT') {
    console.error(`File not found: ${filePath}`);
    process.exit(2);
  }
  throw err;
}

const mapping = ext ? EXT_MAP[ext] : undefined;
if (!mapping) {
  fail({
    ...base,
    reason: ext
      ? `不支持的文件类型 .${ext}。请使用 NotebookLM Web 端上传不支持 OpenAPI 的类型。`
      : '文件无扩展名且未提供 --content-type，无法识别类型。',
  });
}

const fileSize = stat.size;
if (fileSize > DEFAULT_SIZE_LIMIT) {
  fail({
    ...base,
    file_size: fileSize,
    source_type: mapping.source_type,
    content_type: mapping.content_type,
    reason: `文件大小超过 ${DEFAULT_SIZE_LIMIT / MB} MB 限制。`,
  });
}

console.log(
  JSON.stringify({
    pass: true,
    ...base,
    file_size: fileSize,
    source_type: mapping.source_type,
    content_type: inputContentType || mapping.content_type,
  }),
);
process.exit(0);
