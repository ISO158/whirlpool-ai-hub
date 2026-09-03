import os
import threading
import webbrowser
import uvicorn
from src.api.server import app

def open_browser():
    """Abre automaticamente a interface no navegador padrão."""
    try:
        webbrowser.open("http://127.0.0.1:8000")
    except Exception:
        pass

def main():
    print("=" * 70)
    print("   WHIRLPOOL AI OPERATIONS PORTAL - WEB APPLICATION & API   ")
    print("=" * 70)
    print("🔗 Portal do Usuário: http://127.0.0.1:8000")
    print("📖 Documentação da API (Swagger): http://127.0.0.1:8000/docs")
    print("Para encerrar o servidor, pressione Ctrl + C no terminal.")
    print("=" * 70)

    # Abre a página 1.5s após inicializar
    threading.Timer(1.5, open_browser).start()

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    main()
