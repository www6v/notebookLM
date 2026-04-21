@echo off
rem Local overrides (same keys as backend-env.sh). Call with: call "%~dp0win-backend-env.bat"

set "REDIS_URL=redis://127.0.0.1:6379/0"
set "CELERY_BROKER_URL=redis://127.0.0.1:6379/1"
set "CELERY_RESULT_BACKEND_URL=redis://127.0.0.1:6379/2"
set "CACHE_REDIS_URL=redis://127.0.0.1:6379/3"
set "TASK_EVENT_REDIS_URL=redis://127.0.0.1:6379/4"
rem Overrides repo .env (often redis://redis:6379/5 for Docker).
set "GENERATION_RATE_LIMIT_REDIS_URL=redis://127.0.0.1:6379/5"

rem yt-dlp (used by Celery tasks that fetch video metadata).
set "YTDLP_COOKIES_FILE=%USERPROFILE%\Downloads\workspacePy\mycode\notebookLM-ext\cookies.txt"

rem MySQL on remote host (overrides .env docker hostname mysql).
set "DATABASE_URL=mysql+aiomysql://notebooklm:notebooklm@124.221.28.203:3306/notebooklm"

set "MILVUS_URI=http://124.221.28.203:19530"
set "DEER_FLOW_BASE_URL=http://47.118.30.86:2026"
