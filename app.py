import os
import uuid
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from main import run_pipeline

app = FastAPI(title="Video Silence Cutter Web API")

# Serve static files
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

def cleanup_files(paths):
    for path in paths:
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                print(f"Error removing {path}: {e}")

@app.post("/api/process-video")
async def process_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # Create temporary files
    session_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1] or ".mp4"
    input_path = f"temp_in_{session_id}{ext}"
    output_path = f"temp_out_{session_id}{ext}"

    try:
        # Save uploaded file
        with open(input_path, "wb") as f:
            f.write(await file.read())

        # Run processing pipeline
        run_pipeline(input_path, output_path, model_size="small")

        # Return the processed file and schedule cleanup
        background_tasks.add_task(cleanup_files, [input_path, output_path])
        return FileResponse(
            path=output_path,
            filename=f"edited_{file.filename}",
            media_type="video/mp4"
        )
    except Exception as e:
        # If there's an error before returning FileResponse, clean up manually
        cleanup_files([input_path, output_path])
        raise e
