"""
Module Name: Import Users Script
Description: Bulk imports users from a text file into the UGL database.
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

import os
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.scripts.create_user import create_user


def import_from_file(file_path: str):
    """Reads a file and creates users for each line (format: email password)."""
    if not os.path.exists(file_path):
        print(f"[✖] File {file_path} not found.")
        return

    with open(file_path, "r") as f:
        lines = f.readlines()

    import_count = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Split by whitespace
        parts = line.split()
        if len(parts) < 2:
            print(f"[!] Skipping invalid line: {line}")
            continue
        
        email = parts[0]
        password = parts[1]
        
        # Grant admin status to specific user
        is_admin = (email == "juande.molina@ugl.com")
        
        print(f"[*] Importing {email}...")
        if create_user(email, password, is_admin):
            import_count += 1
            
    print(f"\n[✔] Import process finished. {import_count} users imported.")


if __name__ == "__main__":
    # Default path relative to workspace root
    default_path = "/home/juande/UGL/users.txt"
    cli_path = sys.argv[1] if len(sys.argv) > 1 else default_path
    
    # Resolve absolute path
    abs_path = Path(cli_path).resolve()
    if not abs_path.exists():
        # Fallback to local script relative path
        abs_path = (Path(__file__).resolve().parent / cli_path).resolve()

    import_from_file(str(abs_path))
