from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from enkacard import encbanner
import asyncio
import os

app = FastAPI()

# === fungsi bikin banner card ===
async def make_banner(uid: str):
    async with encbanner.ENC(uid=uid) as encard:
        result = await encard.creat()
        filename = f"banner_{uid}.png"
        result.card[0].card.save(filename)  # ambil card pertama saja
        return filename

# === fungsi bikin profile card ===
async def make_profile(uid: str):
    async with encbanner.ENC(uid=uid) as encard:
        result = await encard.profile(card=True)
        filename = f"profile_{uid}.png"
        result.card.save(filename)
        return filename

# === update data enkanetwork ===
@app.get("/update")
async def update_data():
    await encbanner.update()
    return JSONResponse({"status": "✔ data enkanetwork sudah diupdate"})

# === endpoint banner ===
@app.get("/banner")
async def banner(uid: str):
    filename = await make_banner(uid)
    return FileResponse(filename, media_type="image/png")

# === endpoint profile ===
@app.get("/profile")
async def profile(uid: str):
    filename = await make_profile(uid)
    return FileResponse(filename, media_type="image/png")
