from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import os
from ai.llm_inference import ClaudeInference
from database.neo4j_handler import Neo4jHandler
import uuid
from datetime import datetime

app = FastAPI(title="Meeting Transcript Upload API")

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)

# Initialize handlers
claude = ClaudeInference()
neo4j_handler = Neo4jHandler()

# Create full-text index for transcripts
neo4j_handler.create_fulltext_index()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.delete("/delete-all-data/")
async def delete_all_data():
    """Delete all data from Neo4j database"""
    try:
        success = neo4j_handler.delete_all_data()
        if success:
            return JSONResponse(
                status_code=200,
                content={"message": "All data deleted successfully"}
            )
        else:
            return JSONResponse(
                status_code=500,
                content={"message": "Failed to delete data"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error deleting data: {str(e)}"}
        )

@app.post("/upload-transcript/")
async def upload_transcript(file: UploadFile = File(...)):
    # Check if the file is a .txt file
    if not file.filename.endswith('.txt'):
        return JSONResponse(
            status_code=400,
            content={"message": "Only .txt files are allowed"}
        )
    
    try:
        # Read the file content
        content = await file.read()
        text_content = content.decode('utf-8')
        
        # Save the file
        file_path = os.path.join("uploads", file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Generate a unique ID for the transcript
        transcript_id = str(uuid.uuid4())
        
        # Store transcript in Neo4j
        metadata = {
            "filename": file.filename,
            "upload_date": datetime.now().isoformat(),
            "file_path": file_path
        }
        transcript_node = neo4j_handler.create_transcript_node(transcript_id, text_content, metadata)
        
        # Send to Claude for analysis
        action_items = claude.analyze_transcript(text_content)
        
        # Store action items in Neo4j
        stored_action_items = []
        for item in action_items:
            item_id = str(uuid.uuid4())
            item["id"] = item_id
            action_node = neo4j_handler.create_action_item(transcript_id, item)
            stored_action_items.append(item)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "File uploaded and processed successfully",
                "filename": file.filename,
                "file_path": file_path,
                "transcript_id": transcript_id,
                "created_at": metadata["created_at"],
                "updated_at": metadata["updated_at"],
                "action_items": stored_action_items
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error processing file: {str(e)}"}
        )

@app.get("/search-transcripts/")
async def search_transcripts(query: str, limit: int = 5):
    """Search for similar transcripts using RAG"""
    try:
        results = neo4j_handler.search_similar_transcripts(query, limit)
        return JSONResponse(
            status_code=200,
            content={
                "message": "Search completed successfully",
                "results": results
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error searching transcripts: {str(e)}"}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 