from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from enkacard import encbanner
import asyncio
import os
import re
from pathlib import Path

# === init app dengan root_path biar Railway gak 404 di "/" ===
app = FastAPI(root_path=os.getenv("RAILWAY_STATIC_URL", "/"))

# === folder output biar file tersimpan rapi ===
OUTDIR = Path("output")
OUTDIR.mkdir(exist_ok=True)

def safe_name(s: str) -> str:
    return re.sub(r'[^A-Za-z0-9_.-]', '_', str(s))

# === fungsi bikin banner card ===
async def make_banner(uid: str):
    async with encbanner.ENC(uid=uid) as encard:
        result = await encard.creat()
        if not result or not getattr(result, "card", None):
            return None
        filename = OUTDIR / f"banner_{uid}_{safe_name(result.card[0].name)}.png"
        result.card[0].card.save(filename)  # ambil card pertama saja
        return str(filename)

# === fungsi bikin profile card ===
async def make_profile(uid: str):
    async with encbanner.ENC(uid=uid) as encard:
        result = await encard.profile(card=True)
        if not result or not getattr(result, "card", None):
            return None
        filename = OUTDIR / f"profile_{uid}_{safe_name(result.player.name)}.png"
        result.card.save(filename)
        return str(filename)

# === endpoint root ===
@app.get("/")
async def root():
    return {"message": "✅ EnkaCard API aktif. Gunakan /banner?uid=xxxx atau /profile?uid=xxxx"}

# === update data enkanetwork ===
@app.get("/update")
async def update_data():
    try:
        await encbanner.update()
        return JSONResponse({"status": "✔ data enkanetwork sudah diupdate"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# === endpoint banner ===
@app.get("/banner")
async def banner(uid: str):
    filename = await make_banner(uid)
    if not filename or not os.path.exists(filename):
        return JSONResponse(status_code=404, content={"error": f"Banner tidak tersedia untuk UID {uid}"})
    return FileResponse(filename, media_type="image/png", filename=os.path.basename(filename))

# === endpoint profile ===
@app.get("/profile")
async def profile(uid: str):
    filename = await make_profile(uid)
    if not filename or not os.path.exists(filename):
        return JSONResponse(status_code=404, content={"error": f"Profile tidak tersedia untuk UID {uid}"})
    return FileResponse(filename, media_type="image/png", filename=os.path.basename(filename))
