"""
FastAPI server for Pharmacy AI Agent

This is the main server file that handles HTTP requests and streaming responses.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict
import json
import asyncio
import sqlite3
import os

from agent import run_agent_streaming
from tools import get_db_connection

app = FastAPI(title="Pharmacy AI Agent API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    model: str = "gpt-5-mini" 

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Pharmacy AI Agent",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/users")
async def get_users():
    """Get list of all users"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, name, email FROM users ORDER BY id')
        users = cursor.fetchall()
        conn.close()

        users_list = [
            {
                'id': user['id'],
                'name': user['name'],
                'email': user['email']
            }
            for user in users
        ]

        return {
            'success': True,
            'users': users_list,
            'count': len(users_list)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")

@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint with streaming responses.

    Accepts a list of messages and returns a streaming response.
    """
    try:
        # Convert Pydantic models to dictionaries
        messages = [msg.model_dump() for msg in request.messages]

        async def generate():
            """Generator for streaming responses"""
            try:
                async for chunk in run_agent_streaming(messages, request.model):
                    # Send chunk as Server-Sent Event
                    yield f"data: {json.dumps(chunk)}\n\n"
                    await asyncio.sleep(0)  # Allow other tasks to run

                
               

            except Exception as e:
                error_chunk = {
                    'type': 'error',
                    'error': str(e)
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/medications")
async def list_medications():
    """Get list of all medications"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM medications')
        results = cursor.fetchall()
        conn.close()

        medications = [
            {
                'id': row['id'],
                'name': row['name'],
                'active_ingredient': row['active_ingredient'],
                'dosage': row['dosage'],
                'requires_prescription': bool(row['requires_prescription']),
                'in_stock': bool(row['in_stock']),
                'category': row['category']
            }
            for row in results
        ]

        return {'medications': medications}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
