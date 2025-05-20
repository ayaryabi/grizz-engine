#!/usr/bin/env python3
"""
Launcher script to run both the FastAPI server and LLM workers.

Usage:
    python launcher.py [--workers N]

Options:
    --workers N    Number of worker processes to start (default: 2)
"""
import argparse
import asyncio
import os
import signal
import subprocess
import sys
import time
from typing import List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("launcher")

# Global list of worker processes
worker_processes: List[subprocess.Popen] = []
web_process = None

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Launch API server and workers")
    parser.add_argument(
        "--workers",
        type=int,
        default=2,
        help="Number of worker processes to start (default: 2)"
    )
    return parser.parse_args()

def start_web_server() -> subprocess.Popen:
    """Start the FastAPI web server"""
    logger.info("Starting web server...")
    env = os.environ.copy()
    
    # Use uvicorn to run the server
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "main:app", 
        "--host", "0.0.0.0",
        "--port", "8000",
        "--log-level", "info",
    ]
    
    # Start process
    process = subprocess.Popen(
        cmd,
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,  # Line buffered
    )
    
    logger.info(f"Web server started with PID {process.pid}")
    return process

def start_worker(worker_id: int) -> subprocess.Popen:
    """Start a worker process"""
    logger.info(f"Starting worker {worker_id}...")
    env = os.environ.copy()
    env["WORKER_ID"] = f"worker-{worker_id}"
    
    # Python path for worker
    cmd = [
        sys.executable, "-m", "app.workers.llm_worker"
    ]
    
    # Start process
    process = subprocess.Popen(
        cmd,
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,  # Line buffered
    )
    
    logger.info(f"Worker {worker_id} started with PID {process.pid}")
    return process

def handle_output(process: subprocess.Popen, prefix: str):
    """Handle process output in a non-blocking way"""
    if process.stdout:
        while True:
            line = process.stdout.readline()
            if not line:
                break
            sys.stdout.write(f"{prefix}: {line}")
            sys.stdout.flush()

def cleanup(sig=None, frame=None):
    """Clean up all processes on exit"""
    logger.info("Cleaning up processes...")
    
    # Clean up web server
    if web_process:
        try:
            web_process.terminate()
            logger.info(f"Terminated web server (PID {web_process.pid})")
        except:
            pass
    
    # Clean up worker processes
    for i, proc in enumerate(worker_processes):
        try:
            proc.terminate()
            logger.info(f"Terminated worker {i} (PID {proc.pid})")
        except:
            pass
    
    logger.info("All processes terminated")
    sys.exit(0)

async def monitor_processes():
    """Monitor processes and restart them if they exit unexpectedly"""
    global web_process, worker_processes
    
    while True:
        # Check web server
        if web_process and web_process.poll() is not None:
            logger.warning(f"Web server (PID {web_process.pid}) exited with code {web_process.returncode}")
            logger.info("Restarting web server...")
            web_process = start_web_server()
        
        # Check worker processes
        for i, proc in enumerate(worker_processes):
            if proc.poll() is not None:
                logger.warning(f"Worker {i} (PID {proc.pid}) exited with code {proc.returncode}")
                logger.info(f"Restarting worker {i}...")
                worker_processes[i] = start_worker(i)
        
        # Handle output from processes
        if web_process:
            handle_output(web_process, "WEB")
        for i, proc in enumerate(worker_processes):
            handle_output(proc, f"WORKER-{i}")
        
        # Sleep before checking again
        await asyncio.sleep(1)

def main():
    """Main entry point"""
    args = parse_args()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    # Start web server
    global web_process
    web_process = start_web_server()
    
    # Start worker processes
    global worker_processes
    for i in range(args.workers):
        worker = start_worker(i)
        worker_processes.append(worker)
    
    # Print summary
    logger.info(f"Started web server (PID {web_process.pid}) and {len(worker_processes)} workers")
    
    try:
        # Monitor processes
        asyncio.run(monitor_processes())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        cleanup()

if __name__ == "__main__":
    main() 