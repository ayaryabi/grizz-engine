#!/usr/bin/env python3
"""
Minimal test app for Fly.io to debug binding issues
"""
import socket
import os
import sys
import logging
from fastapi import FastAPI
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fly-test")

# Create a minimal app
app = FastAPI()

@app.get("/")
async def root():
    # Get hostname and IP info for debugging
    hostname = socket.gethostname()
    try:
        ip_info = socket.gethostbyname_ex(hostname)
    except:
        ip_info = "Could not get IP info"
    
    return {
        "status": "running",
        "message": "Fly.io test app is running!",
        "hostname": hostname,
        "ip_info": str(ip_info),
        "bound_to": f"{os.environ.get('HOST', '0.0.0.0')}:{os.environ.get('PORT', '8000')}"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    # Log binding information
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    
    logger.info(f"Starting minimal test server on {host}:{port}")
    logger.info(f"Hostname: {socket.gethostname()}")
    logger.info(f"Python version: {sys.version}")
    
    # Try to bind a socket as a test
    test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        test_socket.bind((host, port))
        logger.info(f"Socket binding test successful on {host}:{port}")
        test_socket.close()
    except Exception as e:
        logger.error(f"Socket binding test failed: {e}")
        sys.exit(1)
    
    # Run with proper host binding
    uvicorn.run("fly_test:app", host=host, port=port) 