import os
import sys
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import io
import base64
import subprocess
import asyncio

# Import project modules
from src.graph import OutReachAutomation
from src.tools.leads_loader.file_loader import FileLeadLoader
from src.tools.google_docs_tools import GoogleDocsManager

# Load environment variables
load_dotenv()

app = FastAPI(title="InsightFlow AI Backend")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instance of GoogleDocsManager to reuse credentials
docs_manager = None

@app.on_event("startup")
async def startup_event():
    global docs_manager
    try:
        docs_manager = GoogleDocsManager()
        print("GoogleDocsManager initialized successfully.")
    except Exception as e:
        print(f"Warning: Failed to initialize GoogleDocsManager: {e}")

@app.post("/upload")
async def upload_file_for_analysis(file: UploadFile = File(...)):
    """
    Uploads a file with its original filename and returns a file_id.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
        
    try:
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Sanitize filename to prevent path traversal
        safe_filename = os.path.basename(file.filename)
        file_path = os.path.join(uploads_dir, safe_filename)
        
        # Save file with original name
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Encode the path as file_id
        file_id = base64.urlsafe_b64encode(file_path.encode()).decode()
        
        return {"status": "success", "file_id": file_id, "filename": safe_filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.websocket("/ws/analyze/{file_id}")
async def websocket_analyze(websocket: WebSocket, file_id: str):
    await websocket.accept()
    
    tmp_path = ""
    try:
        # Decode file_id to get path
        tmp_path = base64.urlsafe_b64decode(file_id.encode()).decode()
        
        if not os.path.exists(tmp_path):
            await websocket.send_text("Error: File not found or expired.")
            await websocket.close()
            return

        await websocket.send_text("Starting analysis process...")
        
        # Run main.py as a subprocess
        current_dir = os.path.dirname(os.path.abspath(__file__))
        main_script = os.path.join(current_dir, "main.py")
        
        # Use the same python interpreter
        python_exe = sys.executable
        
        process = subprocess.Popen(
            [python_exe, main_script, tmp_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
            cwd=current_dir
        )
        
        processed_file_path = None
        
        # Stream output
        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            if line:
                # Check for special output marker
                if line.startswith("OUTPUT_FILE:"):
                    processed_file_path = line.replace("OUTPUT_FILE:", "").strip()
                else:
                    await websocket.send_text(line)
                    
        process.stdout.close()
        return_code = process.wait()
        
        if return_code != 0:
            await websocket.send_text(f"Error: Process exited with code {return_code}")
        else:
            await websocket.send_text("Analysis complete.")
            
            if processed_file_path and os.path.exists(processed_file_path):
                await websocket.send_text("Uploading processed file to Drive...")
                
                processed_filename = os.path.basename(processed_file_path)
                
                global docs_manager
                if not docs_manager:
                    docs_manager = GoogleDocsManager()
                    
                drive_link = docs_manager.upload_file(
                    processed_file_path, 
                    processed_filename, 
                    "InsightFlow_Processed_Files", 
                    make_shareable=True
                )
                
                if drive_link:
                    # Send a structured JSON message for the final result
                    result_msg = {
                        "type": "COMPLETED",
                        "drive_link": drive_link,
                        "filename": processed_filename
                    }
                    await websocket.send_json(result_msg)
                else:
                    await websocket.send_text("Error: Failed to upload to Drive.")
                    
                # Clean up processed file
                try:
                    os.unlink(processed_file_path)
                except:
                    pass
            else:
                await websocket.send_text("Error: Processed file not found.")

    except WebSocketDisconnect:
        print("Client disconnected")
        if 'process' in locals() and process.poll() is None:
            process.terminate()
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_text(f"Error: {str(e)}")
        except:
            pass
    finally:
        # Clean up input file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except:
                pass
        try:
            await websocket.close()
        except:
            pass

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
