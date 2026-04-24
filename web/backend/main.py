import os
import json
import asyncio
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from downloader import Downloader

app = FastAPI(title="Music Downloader API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global queue for SSE
event_queue = asyncio.Queue()

class DownloadRequest(BaseModel):
    url: str
    format: str = "mp3"
    quality: str = "192"
    folder: str = "downloads"

async def progress_callback(data):
    await event_queue.put(data)

@app.get("/api/folders")
async def list_folders():
    # List folders in the project root and some common ones
    root = os.path.abspath(os.path.join(os.getcwd(), "..", ".."))
    folders = []
    try:
        for item in os.listdir(root):
            path = os.path.join(root, item)
            if os.path.isdir(path) and not item.startswith("."):
                folders.append({"name": item, "path": path})
    except:
        pass
    return folders

@app.post("/api/download")
async def start_download(req: DownloadRequest, background_tasks: BackgroundTasks):
    loop = asyncio.get_event_loop()
    downloader = Downloader(progress_callback=progress_callback, loop=loop)
    
    # Resolve output directory
    if os.path.isabs(req.folder):
        out_dir = req.folder
    else:
        out_dir = os.path.abspath(os.path.join(os.getcwd(), "..", "..", req.folder))
    
    background_tasks.add_task(downloader.download, req.url, out_dir, req.format, req.quality)
    return {"message": "Download started"}

@app.get("/api/events")
async def event_stream(request: Request):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            
            try:
                # Wait for an event from the queue
                data = await asyncio.wait_for(event_queue.get(), timeout=1.0)
                yield f"data: {json.dumps(data)}\n\n"
            except asyncio.TimeoutError:
                # Keep alive
                yield ": keep-alive\n\n"
            except Exception as e:
                print(f"SSE Error: {e}")
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
