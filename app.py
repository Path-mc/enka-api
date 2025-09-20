from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from enkacard import encbanner
import asyncio
import os
import re
from pathlib import Path

app = FastAPI()

OUTDIR = Path("output")
OUTDIR.mkdir(exist_ok=True)

def safe_name(s: str) -> str:
    return re.sub(r'[^A-Za-z0-9_.-]', '_', str(s))

# --- update enkanetwork once at startup (may take a while on first run) ---
# Run update in background to prevent startup timeout
async def background_update():
    try:
        print("🔄 Updating enkanetwork data (first run may download many files)...")
        await encbanner.update()
        print("✅ enkanetwork update finished")
    except Exception as e:
        # don't crash server — just log
        print("⚠️ enkanetwork.update() failed:", e)

@app.on_event("startup")
async def startup_event():
    # Start the update in background without waiting for it
    asyncio.create_task(background_update())

# --- helper to create banners safely ---
async def make_banner_files(uid: str):
    async with encbanner.ENC(uid=uid) as encard:
        result = await encard.creat()
        # safety checks
        if not result or not getattr(result, "card", None):
            return None
        saved = []
        for i, card in enumerate(result.card, start=1):
            filename = OUTDIR / f"banner_{uid}_{i}_{safe_name(card.name)}.png"
            card.card.save(filename)
            saved.append(str(filename))
        return saved

# --- helper to create profile image safely ---
async def make_profile_file(uid: str):
    async with encbanner.ENC(uid=uid) as encard:
        result = await encard.profile(card=True)
        if not result or not getattr(result, "card", None):
            return None
        filename = OUTDIR / f"profile_{uid}_{safe_name(result.player.name)}.png"
        result.card.save(filename)
        return str(filename)

# --- root ---
@app.get("/")
async def root():
    return {"message": "EnkaCard API aktif 🚀. endpoint: /banner?uid=NUMERIC_UID  /profile?uid=NUMERIC_UID /debug?uid=NUMERIC_UID"}

# --- banner endpoint: return first card image directly ---
@app.get("/banner")
async def banner(uid: str):
    try:
        files = await make_banner_files(uid)
        if not files:
            return JSONResponse(status_code=404, content={"error": f"UID {uid} tidak ditemukan / profile private / tidak ada card"})
        return FileResponse(files[0], media_type="image/png", filename=os.path.basename(files[0]))
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# --- profile endpoint: return profile image directly ---
@app.get("/profile")
async def profile(uid: str):
    try:
        fname = await make_profile_file(uid)
        if not fname or not Path(fname).exists():
            return JSONResponse(status_code=404, content={"error": f"Profile not available for UID {uid}"})
        return FileResponse(fname, media_type="image/png", filename=os.path.basename(fname))
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# --- debug endpoint to inspect result quickly ---
@app.get("/debug")
async def debug(uid: str):
    try:
        async with encbanner.ENC(uid=uid) as encard:
            result = await encard.creat()
            info = {
                "result_repr": repr(result),
                "has_card": bool(getattr(result, "card", None))
            }
            if getattr(result, "card", None):
                info["card_count"] = len(result.card)
                info["card_names"] = [c.name for c in result.card]
            return info
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Run with uvicorn when script is executed directly
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
