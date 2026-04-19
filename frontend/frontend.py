"""
Module Name: Application Entry Point
Description: Direct runner for the frontend client application.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
