"""
Module Name: Import Users Script
Description:
    Lee un archivo de texto (por defecto users.txt) e importa los usuarios
    en la base de datos de UGL.
    Formato esperado: email password
Author: Juande Molina
Copyright: (c) 2026 JuandeMolina
License: MIT
"""

import sys
import os
from pathlib import Path

# Añadir el directorio backend al path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.scripts.create_user import create_user


def import_from_file(file_path: str):
    if not os.path.exists(file_path):
        print(f"[✖] El archivo {file_path} no existe.")
        return

    with open(file_path, "r") as f:
        lines = f.readlines()

    count = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # El archivo parece estar separado por espacios o tabs
        parts = line.split()
        if len(parts) < 2:
            print(f"[!] Saltando línea inválida: {line}")
            continue
        
        email = parts[0]
        password = parts[1]
        
        # Juande es admin
        is_admin = (email == "juande.molina@ugl.com")
        
        print(f"[*] Importando {email}...")
        if create_user(email, password, is_admin):
            count += 1
            
    print(f"\n[✔] Proceso finalizado. {count} usuarios importados.")


if __name__ == "__main__":
    # El archivo users.txt está en la raíz del proyecto /home/juande/UGL/
    default_path = "../../users.txt"
    path = sys.argv[1] if len(sys.argv) > 1 else default_path
    
    # Resolver ruta absoluta si es relativa a este script
    abs_path = Path(__file__).resolve().parent / path
    if not abs_path.exists():
        # Intentar ruta relativa al CWD
        abs_path = Path(path).resolve()

    import_from_file(str(abs_path))
