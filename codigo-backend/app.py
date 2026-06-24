import os
import sys

# Esto le enseña a Python a buscar dentro de tu estructura de carpetas
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Importamos la aplicación de Flask desde tu archivo interno
from app import app

if __name__ == "__main__":
    # Render necesita obligatoriamente tomar el puerto dinámico de esta variable
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
