#!/usr/bin/env python3
"""
A simple script to check if the server can bind to the specified host and port.
Run this before deploying to make sure the binding works.
"""
import socket
import os
import sys

def check_port_binding(host, port):
    """Check if we can bind a socket to the specified host:port"""
    print(f"Attempting to bind to {host}:{port}...")
    
    try:
        # Create a socket object
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Allow reuse of the address (in case it was recently used)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Bind to the port
        s.bind((host, port))
        
        # Listen for connections
        s.listen(1)
        
        print(f"✅ Successfully bound to {host}:{port}")
        return True
    
    except Exception as e:
        print(f"❌ Failed to bind to {host}:{port}: {e}")
        return False
    
    finally:
        # Close the socket
        try:
            s.close()
        except:
            pass

if __name__ == "__main__":
    # Get host and port from environment variables or use defaults
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    
    print(f"System information:")
    print(f"- Python version: {sys.version}")
    print(f"- Operating system: {os.name}")
    
    # Check the binding
    success = check_port_binding(host, port)
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1) 