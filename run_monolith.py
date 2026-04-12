from werkzeug.serving import run_simple
from wsgi import application

if __name__ == "__main__":
    print("\n" + "="*50)
    print("Iniciando UGL en modo SERVIDOR ÚNICO (Puerto 5000)")
    print("  => Frontend disponible en: http://localhost:5000/")
    print("  => API Backend disponible en: http://localhost:5000/api")
    print("="*50 + "\n")
    
    # run_simple monta la aplicación WSGI en el puerto especificado
    run_simple(
        hostname="0.0.0.0", 
        port=5000, 
        application=application, 
        use_reloader=True, 
        use_debugger=True
    )
