import subprocess
import os
import sys
import time

def start():
    root = os.path.dirname(os.path.abspath(__file__))
    
    backend_dir = os.path.join(root, "web", "backend")
    frontend_dir = os.path.join(root, "web", "frontend")

    print("🚀 Iniciando Music Downloader Web...")

    # Start Backend
    print("📦 Iniciando Backend (FastAPI)...")
    python_exe = os.path.join(root, ".venv", "Scripts", "python.exe") if os.name == "nt" else os.path.join(root, ".venv", "bin", "python")
    backend_process = subprocess.Popen(
        [python_exe, "main.py"],
        cwd=backend_dir
    )

    # Start Frontend
    print("🎨 Iniciando Frontend (Vite)...")
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        shell=True
    )

    print("\n✅ Aplicação rodando!")
    print("👉 Backend: http://localhost:8000")
    print("👉 Frontend: http://localhost:5173")
    print("\nPressione Ctrl+C para encerrar.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Encerrando...")
        backend_process.terminate()
        frontend_process.terminate()

if __name__ == "__main__":
    start()
