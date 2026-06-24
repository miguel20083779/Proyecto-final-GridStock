import os
from flask import Flask

# Aquí creamos el motor directamente para evitar problemas de carpetas
app = Flask(__name__)

# ==========================================
# ¡RUTAS DE PRUEBA / BIENVENIDA!
# ==========================================
@app.route('/')
def home():
    return "¡Servidor de GridStock funcionando correctamente en Render!"

# Si tu código real tiene rutas como @app.route('/ventas'), etc.,
# puedes copiarlas y pegarlas aquí abajo.


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
