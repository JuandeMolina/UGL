"""
Module Name: Monolith Runner
Description: Runner script to start both frontend and backend in a single process.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

from werkzeug.serving import run_simple

from wsgi import application

if __name__ == "__main__":
    print("\n" + "="*50)
    print("Starting UGL in MONOLITH mode (Port 5000)")
    print("  => Frontend available at: http://localhost:5000/")
    print("  => Backend API available at: http://localhost:5000/api")
    print("="*50 + "\n")
    
    # run_simple mounts the WSGI application on the specified port
    run_simple(
        hostname="0.0.0.0", 
        port=5000, 
        application=application, 
        use_reloader=True, 
        use_debugger=True
    )
