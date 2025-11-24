import os
import sys
import pandas as pd
import logging
import asyncio
import threading
import base64
from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Import project modules
from src.graph import OutReachAutomation
from src.tools.leads_loader.file_loader import FileLeadLoader
from src.tools.google_docs_tools import GoogleDocsManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

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

class WebSocketLogHandler(logging.Handler):
    """
    Custom logging handler that sends log records to a WebSocket.
    """
    def __init__(self, websocket: WebSocket, loop):
        super().__init__()
        self.websocket = websocket
        self.loop = loop

    def emit(self, record):
        try:
            msg = self.format(record)
            # Schedule the send_text coroutine in the main event loop
            asyncio.run_coroutine_threadsafe(self.websocket.send_text(msg), self.loop)
        except Exception:
            self.handleError(record)

@app.on_event("startup")
async def startup_event():
    global docs_manager
    try:
        docs_manager = GoogleDocsManager()
        logger.info("GoogleDocsManager initialized successfully.")
    except Exception as e:
        logger.warning(f"Failed to initialize GoogleDocsManager: {e}")

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
    
    file_path = ""
    try:
        # Decode file_id to get path
        file_path = base64.urlsafe_b64decode(file_id.encode()).decode()
        
        if not os.path.exists(file_path):
            await websocket.send_text("Error: File not found or expired.")
            await websocket.close()
            return

        await websocket.send_text("Starting analysis process...")
        
        # --- Load Data ---
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file_path)
            else:
                await websocket.send_text("Error: Invalid file format")
                await websocket.close()
                return
        except Exception as e:
            await websocket.send_text(f"Error loading file: {e}")
            await websocket.close()
            return

        # --- Setup Logging to WebSocket ---
        loop = asyncio.get_running_loop()
        ws_handler = WebSocketLogHandler(websocket, loop)
        ws_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s')
        ws_handler.setFormatter(formatter)
        
        # Attach handler to the root logger so we capture logs from all modules
        root_logger = logging.getLogger()
        root_logger.addHandler(ws_handler)
        
        try:
            # --- Column Validation & Normalization (Moved from main.py) ---
            # Normalize existing columns to uppercase for consistent checking
            df.columns = [c.strip().upper() for c in df.columns]
            
            # Ensure STATUS column exists and normalize to empty string
            if "STATUS" not in df.columns:
                logger.info("Adding missing column: STATUS with default: ''")
                df["STATUS"] = ""
            
            # Fill NaN/None values in STATUS with empty string to ensure we catch them
            df["STATUS"] = df["STATUS"].fillna("")
            
            # Ensure other required columns exist
            if "LEAD_SCORE" not in df.columns:
                logger.info("Adding missing column: LEAD_SCORE with default: 0")
                df["LEAD_SCORE"] = 0
            
            if "QUALIFIED" not in df.columns:
                logger.info("Adding missing column: QUALIFIED with default: 'NO'")
                df["QUALIFIED"] = "NO"
            
            logger.info(f"Loaded {len(df)} records.")
            
            # --- Initialize Automation ---
            lead_loader = FileLeadLoader(df)
            
            # Use global docs_manager if available
            global docs_manager
            if not docs_manager:
                docs_manager = GoogleDocsManager()
                
            automation = OutReachAutomation(lead_loader, docs_manager)
            app_graph = automation.app
            
            inputs = {"leads_ids": []}
            config = {"recursion_limit": 1000}
            
            logger.info("Initializing automation graph...")
            
            # --- Run Graph in Thread ---
            # We run the synchronous graph execution in a separate thread
            # to avoid blocking the FastAPI event loop.
            def run_graph():
                return app_graph.invoke(inputs, config)
            
            result = await asyncio.to_thread(run_graph)
            
            logger.info("Analysis complete. Generating output...")
            
            # --- Save Processed File ---
            output_dir = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            output_path = os.path.join(output_dir, f"Processed_{filename}")
            
            # Ensure extension is xlsx for output
            if not output_path.endswith('.xlsx'):
                output_path = os.path.splitext(output_path)[0] + '.xlsx'
            
            # Save the modified dataframe from the loader
            df_to_save = lead_loader.df.copy()
            if "id" in df_to_save.columns and df_to_save["id"].equals(df_to_save.index.astype(str)):
                df_to_save = df_to_save.drop(columns=["id"])
                
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                df_to_save.to_excel(writer, index=False)
                
            logger.info(f"Output saved to: {output_path}")
            
            # --- Upload to Drive ---
            if os.path.exists(output_path):
                await websocket.send_text("Uploading processed file to Drive...")
                
                processed_filename = os.path.basename(output_path)
                
                drive_link = docs_manager.upload_file(
                    output_path, 
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
                    os.unlink(output_path)
                except:
                    pass
            else:
                await websocket.send_text("Error: Processed file not found.")

        except Exception as e:
            logger.error(f"Error during execution: {e}")
            await websocket.send_text(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            # Remove the custom handler
            root_logger.removeHandler(ws_handler)

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Clean up input file
        if file_path and os.path.exists(file_path):
            try:
                os.unlink(file_path)
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
