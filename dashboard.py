import asyncio
import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse

from shad_self_KIA import APP_VERSION, DATA_DIR, SESSION_DIR, STATE, app as shad_client, main as bot_main

app = FastAPI(title="Shad Self Operations Center", version=APP_VERSION)

DATA_PATH = Path(DATA_DIR)
SESSION_PATH = Path(SESSION_DIR)
BACKUP_PATH = DATA_PATH / "backups"
BACKUP_PATH.mkdir(parents=True, exist_ok=True)

MAX_ARCHIVE_BYTES = 50 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 256 * 1024 * 1024
MAX_FILES = 1000
BOT_TASK = None


def _token_ok(token: str | None) -> bool:
    expected = os.getenv("DASHBOARD_TOKEN", "").strip()
    return bool(expected) and token == expected


def require_token(token: str | None) -> None:
    if not _token_ok(token):
        raise HTTPException(status_code=401, detail="Unauthorized")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _manifest() -> dict:
    files = []
    if SESSION_PATH.exists():
        for path in sorted(p for p in SESSION_PATH.rglob("*") if p.is_file()):
            files.append({
                "path": str(path.relative_to(SESSION_PATH)),
                "size": path.stat().st_size,
                "sha256": _sha256(path),
            })
    return {
        "version": APP_VERSION,
        "format_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "file_count": len(files),
        "files": files,
    }


def create_backup() -> Path:
    manifest = _manifest()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    final_path = BACKUP_PATH / f"shad-self-{stamp}.zip"
    tmp_path = BACKUP_PATH / f".{final_path.name}.tmp"

    with zipfile.ZipFile(tmp_path, "x", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        runtime = {
            "version": APP_VERSION,
            "railway_commit": os.getenv("RAILWAY_GIT_COMMIT_SHA"),
            "railway_deployment": os.getenv("RAILWAY_DEPLOYMENT_ID"),
            "railway_environment": os.getenv("RAILWAY_ENVIRONMENT_NAME"),
            "created_at": manifest["created_at"],
        }
        z.writestr("runtime.json", json.dumps(runtime, ensure_ascii=False, indent=2))
        if SESSION_PATH.exists():
            for path in sorted(p for p in SESSION_PATH.rglob("*") if p.is_file()):
                z.write(path, f"sessions/{path.relative_to(SESSION_PATH)}")
    os.replace(tmp_path, final_path)
    return final_path


def validate_archive(path: Path) -> dict:
    if path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("Archive exceeds maximum upload size")

    with zipfile.ZipFile(path, "r") as z:
        bad = z.testzip()
        if bad:
            raise ValueError(f"CRC validation failed: {bad}")
        infos = z.infolist()
        if len(infos) > MAX_FILES + 2:
            raise ValueError("Archive contains too many files")

        total = 0
        for info in infos:
            name = info.filename.replace("\\", "/")
            target = (Path("/safe-root") / name).resolve()
            if not str(target).startswith("/safe-root/"):
                raise ValueError("Path traversal detected")
            mode = (info.external_attr >> 16) & 0o170000
            if mode == 0o120000:
                raise ValueError("Symlink entries are not allowed")
            total += info.file_size
            if total > MAX_UNCOMPRESSED_BYTES:
                raise ValueError("Archive uncompressed size is too large")

        try:
            manifest = json.loads(z.read("manifest.json"))
        except Exception as exc:
            raise ValueError("manifest.json is missing or invalid") from exc

        if manifest.get("format_version") != 1:
            raise ValueError("Unsupported backup format")

        expected = {x["path"]: x for x in manifest.get("files", [])}
        checked = 0
        for info in infos:
            if not info.filename.startswith("sessions/") or info.is_dir():
                continue
            rel = info.filename[len("sessions/"):]
            data = z.read(info)
            meta = expected.get(rel)
            if not meta or len(data) != meta["size"] or hashlib.sha256(data).hexdigest() != meta["sha256"]:
                raise ValueError(f"Checksum validation failed: {rel}")
            checked += 1

        if checked != len(expected):
            raise ValueError("Manifest/file count mismatch")

        return {
            "valid": True,
            "format_version": 1,
            "file_count": checked,
            "uncompressed_bytes": total,
            "version": manifest.get("version"),
            "created_at": manifest.get("created_at"),
        }


def restore_archive(path: Path) -> dict:
    result = validate_archive(path)
    temp_dir = Path(tempfile.mkdtemp(prefix="shad-restore-", dir=DATA_PATH))
    safety = None
    try:
        with zipfile.ZipFile(path, "r") as z:
            for info in z.infolist():
                if not info.filename.startswith("sessions/") or info.is_dir():
                    continue
                target = (temp_dir / info.filename).resolve()
                if not str(target).startswith(str(temp_dir.resolve()) + os.sep):
                    raise ValueError("Unsafe restore path")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(z.read(info))

        if SESSION_PATH.exists():
            safety = DATA_PATH / f"sessions-safety-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
            os.replace(SESSION_PATH, safety)
        os.replace(temp_dir / "sessions", SESSION_PATH)
        return {**result, "restored": True, "safety_backup": str(safety) if safety else None}
    except Exception:
        if safety and not SESSION_PATH.exists():
            os.replace(safety, SESSION_PATH)
        raise
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.get("/", response_class=HTMLResponse)
async def dashboard() -> str:
    return """<!doctype html>
<html lang="fa" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Shad Self Operations Center</title>
<style>
body{font-family:system-ui;background:#0b1020;color:#eef2ff;max-width:1100px;margin:auto;padding:24px}
.card{background:#151c31;border:1px solid #293451;border-radius:16px;padding:18px;margin:12px 0}
button,input{padding:10px;border-radius:10px;border:1px solid #3a4665;background:#0e1528;color:#fff}
button{cursor:pointer}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
pre{white-space:pre-wrap}.ok{color:#67e8a5}.bad{color:#fb7185}
</style></head><body>
<h1>🛡️ Shad Self Operations Center</h1>
<div class="card"><input id="token" type="password" placeholder="Dashboard token"><button onclick="save()">ورود</button></div>
<div class="grid">
<div class="card"><b>Runtime</b><pre id="status">در حال دریافت...</pre></div>
<div class="card"><b>Backup</b><button onclick="backup()">ساخت Backup</button><button onclick="listBackups()">لیست Backupها</button><pre id="backups"></pre></div>
<div class="card"><b>Operations</b><button onclick="restart()">Restart Bot</button><input id="file" type="file" accept=".zip"><button onclick="restore()">Restore</button></div>
</div>
<script>
const key='shad-dashboard-token';
document.getElementById('token').value=sessionStorage.getItem(key)||'';
function save(){sessionStorage.setItem(key,document.getElementById('token').value);refresh()}
async function api(url,opt={}){opt.headers={...(opt.headers||{}),'X-Dashboard-Token':sessionStorage.getItem(key)||''};let r=await fetch(url,opt);let j=await r.json().catch(()=>({}));if(!r.ok)throw new Error(j.detail||r.status);return j}
async function refresh(){try{document.getElementById('status').textContent=JSON.stringify(await api('/api/status'),null,2)}catch(e){document.getElementById('status').textContent='ERROR: '+e}}
async function backup(){try{alert(JSON.stringify(await api('/api/backup',{method:'POST'})));listBackups()}catch(e){alert(e)}}
async function listBackups(){try{document.getElementById('backups').textContent=JSON.stringify(await api('/api/backups'),null,2)}catch(e){document.getElementById('backups').textContent='ERROR: '+e}}
async function restart(){try{alert(JSON.stringify(await api('/api/restart',{method:'POST'})));refresh()}catch(e){alert(e)}}
async function restore(){let f=document.getElementById('file').files[0];if(!f)return alert('Backup را انتخاب کنید');let fd=new FormData();fd.append('file',f);try{alert(JSON.stringify(await api('/api/restore',{method:'POST',body:fd})));}catch(e){alert(e)}}
refresh();listBackups();
</script></body></html>"""


@app.get("/health")
async def health():
    return {"status": "ok", "version": APP_VERSION}


@app.get("/ready")
async def ready():
    if not shad_client.is_connected:
        return JSONResponse(status_code=503, content={"status": "not_ready", "connected": False})
    return {"status": "ready", "connected": True}


@app.get("/api/status")
async def status(x_dashboard_token: str | None = Header(default=None)):
    require_token(x_dashboard_token)
    return {
        "version": APP_VERSION,
        "connected": bool(shad_client.is_connected),
        "uptime_seconds": int(asyncio.get_running_loop().time() - STATE["start"] if STATE.get("start") else 0),
        "messages": STATE["msgs"],
        "commands": STATE["commands"],
        "commit": os.getenv("RAILWAY_GIT_COMMIT_SHA"),
        "deployment": os.getenv("RAILWAY_DEPLOYMENT_ID"),
        "environment": os.getenv("RAILWAY_ENVIRONMENT_NAME"),
    }


@app.post("/api/backup")
async def backup(x_dashboard_token: str | None = Header(default=None)):
    require_token(x_dashboard_token)
    path = await asyncio.to_thread(create_backup)
    return {"created": True, "file": path.name, "size": path.stat().st_size}


@app.get("/api/backups")
async def backups(x_dashboard_token: str | None = Header(default=None)):
    require_token(x_dashboard_token)
    return {"backups": [
        {"name": p.name, "size": p.stat().st_size, "created_at": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat()}
        for p in sorted(BACKUP_PATH.glob("*.zip"), reverse=True)
    ]}


@app.get("/api/backups/{name}")
async def download_backup(name: str, x_dashboard_token: str | None = Header(default=None)):
    require_token(x_dashboard_token)
    path = (BACKUP_PATH / name).resolve()
    if path.parent != BACKUP_PATH.resolve() or path.suffix != ".zip" or not path.is_file():
        raise HTTPException(status_code=404, detail="Backup not found")
    return FileResponse(path, filename=path.name, media_type="application/zip")


@app.post("/api/restore")
async def restore(file: UploadFile = File(...), x_dashboard_token: str | None = Header(default=None)):
    require_token(x_dashboard_token)
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="ZIP backup required")
    tmp = DATA_PATH / ".restore-upload.zip"
    try:
        data = await file.read(MAX_ARCHIVE_BYTES + 1)
        if len(data) > MAX_ARCHIVE_BYTES:
            raise HTTPException(status_code=413, detail="Backup is too large")
        tmp.write_bytes(data)
        result = await asyncio.to_thread(restore_archive, tmp)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        tmp.unlink(missing_ok=True)


@app.post("/api/restart")
async def restart(x_dashboard_token: str | None = Header(default=None)):
    require_token(x_dashboard_token)
    global BOT_TASK
    if BOT_TASK and not BOT_TASK.done():
        BOT_TASK.cancel()
        try:
            await BOT_TASK
        except asyncio.CancelledError:
            pass
    BOT_TASK = asyncio.create_task(bot_main())
    return {"restarted": True}


@app.on_event("startup")
async def startup():
    global BOT_TASK
    BOT_TASK = asyncio.create_task(bot_main())


@app.on_event("shutdown")
async def shutdown():
    global BOT_TASK
    if BOT_TASK and not BOT_TASK.done():
        BOT_TASK.cancel()
        try:
            await BOT_TASK
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
