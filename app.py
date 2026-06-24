from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import json
import copy
import os
from datetime import datetime, date


from pathlib import Path
import webbrowser
import threading
import secrets

app = Flask(__name__, static_folder='../frontend')
CORS(app)

# ==================== CONFIGURACIÓN ====================
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
USERS_FILE = DATA_DIR / "usuarios.json"

active_sessions = {}

# ==================== UTILIDADES ====================
def get_user_data_dir(username):
    user_dir = DATA_DIR / username
    user_dir.mkdir(exist_ok=True)
    return user_dir

def load_data(username, file_key, default=None):
    user_dir = get_user_data_dir(username)
    file_path = user_dir / f"{file_key}.json"
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    if default is None:
        return {}
    return copy.deepcopy(default)

def save_data(username, file_key, data):
    user_dir = get_user_data_dir(username)
    file_path = user_dir / f"{file_key}.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_global_data(file_key, default=None):
    file_path = DATA_DIR / f"{file_key}.json"
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    if default is None:
        return {}
    return copy.deepcopy(default)

def save_global_data(file_key, data):
    file_path = DATA_DIR / f"{file_key}.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_user_from_token():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token in active_sessions:
        return active_sessions[token]['username']
    return None

def today_iso():
    return date.today().isoformat()

def now_iso():
    return datetime.now().isoformat()

# ==================== RUTAS ESTÁTICAS ====================
@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('../frontend', filename)

# ==================== INVENTARIO ====================
@app.route('/api/inventario', methods=['GET'])
def get_inventario():
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "No autorizado"}), 401
    return jsonify(load_data(user, 'inventario', {}))

@app.route('/api/inventario/<codigo>', methods=['GET'])
def get_producto(codigo):
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "No autorizado"}), 401
    productos = load_data(user, 'inventario', {})
    producto = productos.get(codigo)
    if producto:
        return jsonify(producto)
    return jsonify({"success": False, "message": "Producto no encontrado"}), 404

@app.route('/api/inventario', methods=['POST'])
def agregar_producto():
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "No autorizado"}), 401
    
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "Datos vacíos"}), 400
        
        codigo = data.get('codigo', '').strip()
        nombre = data.get('nombre', '').strip()
        precio = data.get('precio')
        cantidad = data.get('cantidad')
        
        if not codigo or not nombre:
            return jsonify({"success": False, "message": "Código y nombre requeridos"}), 400
        
        if precio is None or cantidad is None:
            return jsonify({"success": False, "message": "Precio y cantidad requeridos"}), 400
        
        try:
            precio = float(precio)
            cantidad = int(cantidad)
            umbral_minimo = int(data.get('umbral_minimo', 10))
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Precio debe ser número, cantidad debe ser entero"}), 400
        
        if precio < 0 or cantidad < 0 or umbral_minimo < 0:
            return jsonify({"success": False, "message": "Los valores no pueden ser negativos"}), 400
        
        productos = load_data(user, 'inventario', {})
        if codigo in productos:
            return jsonify({"success": False, "message": "El producto ya existe"}), 400
        
        productos[codigo] = {
            "nombre": nombre,
            "precio": precio,
            "cantidad": cantidad,
            "umbral_minimo": umbral_minimo,
            "fecha_actualizacion": now_iso()
        }
        save_data(user, 'inventario', productos)
        return jsonify({"success": True, "message": "Producto agregado"})
    
    except Exception as e:
        return jsonify({"success": False, "message": f"Error interno: {str(e)}"}), 500

@app.route('/api/inventario/<codigo>', methods=['PUT'])
def actualizar_producto(codigo):
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "No autorizado"}), 401
    data = request.json
    productos = load_data(user, 'inventario', {})
    if codigo not in productos:
        return jsonify({"success": False, "message": "Producto no encontrado"}), 404
    prod = productos[codigo]
    for key in ['nombre', 'precio', 'cantidad', 'umbral_minimo']:
        if key in data:
            if key == 'nombre':
                prod[key] = str(data[key]).strip()
            elif key == 'precio':
                prod[key] = float(data[key])
            else:
                prod[key] = int(data[key])
    prod["fecha_actualizacion"] = now_iso()
    save_data(user, 'inventario', productos)
    return jsonify({"success": True, "message": "Producto actualizado"})

@app.route('/api/inventario/<codigo>', methods=['DELETE'])
def eliminar_producto(codigo):
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "No autorizado"}), 401
    productos = load_data(user, 'inventario', {})
    if codigo not in productos:
        return jsonify({"success": False, "message": "Producto no encontrado"}), 404
    del productos[codigo]
    save_data(user, 'inventario', productos)
    return jsonify({"success": True, "message": "Producto eliminado"})

@app.route('/api/inventario/alertas', methods=['GET'])
def get_alertas():
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "No autorizado"}), 401
    productos = load_data(user, 'inventario', {})
    alertas = []
    for codigo, prod in productos.items():
        if prod["cantidad"] <= prod["umbral_minimo"]:
            alertas.append({
                "codigo": codigo,
                "nombre": prod["nombre"],
                "cantidad": prod["cantidad"],
                "umbral_minimo": prod["umbral_minimo"],
                "necesario": prod["umbral_minimo"] - prod["cantidad"] + 5
            })
    return jsonify(alertas)

# ==================== VENTAS ====================
@app.route('/api/ventas', methods=['GET'])
def get_ventas():
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "No autorizado"}), 401
    return jsonify(load_data(user, 'ventas', []))

def filter_sales_by_date(sales, year=None, month=None, day=None):
    filtered = []
    for v in sales:
        dt = datetime.fromisoformat(v["fecha"])
        if (year is None or dt.year == year) and (month is None or dt.month == month) and (day is None or dt.day == day):
            filtered.append(v)
    return filtered

@app.route('/api/ventas/hoy', methods=['GET'])
def get_ventas_hoy():
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "No autorizado"}), 401
    ventas = load_data(user, 'ventas', [])
    hoy = today_iso()
    ventas_hoy = [v for v in ventas if v["fecha"].startswith(hoy)]
    return jsonify(ventas_hoy)

@app.route('/api/ventas/mes', methods=['GET'])
def get_ventas_mes():
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "No autorizado"}), 401
    ventas = load_data(user, 'ventas', [])
    year = request.args.get('año', type=int, default=date.today().year)
    month = request.args.get('mes', type=int, default=date.today().month)
    ventas_mes = filter_sales_by_date(ventas, year=year, month=month)
    return jsonify(ventas_mes)

@app.route('/api/ventas/total-hoy', methods=['GET'])
def get_total_hoy():
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "No autorizado"}), 401
    ventas = load_data(user, 'ventas', [])
    hoy = today_iso()
    total = sum(v["total"] for v in ventas if v["fecha"].startswith(hoy))
    return jsonify({"total": total})

@app.route('/api/ventas/total-mes', methods=['GET'])
def get_total_mes():
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "No autorizado"}), 401
    ventas = load_data(user, 'ventas', [])
    year = request.args.get('año', type=int, default=date.today().year)
    month = request.args.get('mes', type=int, default=date.today().month)
    ventas_mes = filter_sales_by_date(ventas, year=year, month=month)
    total = sum(v["total"] for v in ventas_mes)
    return jsonify({"total": total})

@app.route('/api/ventas', methods=['POST'])
def registrar_venta():
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "No autorizado"}), 401
    
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "Datos vacíos"}), 400
        
        productos_venta = data.get('productos', [])
        if not productos_venta:
            return jsonify({"success": False, "message": "No hay productos en la venta"}), 400
        
        total = 0
        venta_items = []
        productos_inv = load_data(user, 'inventario', {})

        for item in productos_venta:
            try:
                codigo = item.get('codigo')
                cantidad = int(item.get('cantidad', 0))
                
                if not codigo or cantidad < 1:
                    return jsonify({"success": False, "message": f"Producto inválido: {codigo}"}), 400

                if codigo not in productos_inv:
                    return jsonify({"success": False, "message": f"Producto {codigo} no encontrado"}), 400

                prod = productos_inv[codigo]
                if prod['cantidad'] < cantidad:
                    return jsonify({"success": False, "message": f"Stock insuficiente para {prod['nombre']}"}), 400

                subtotal = float(prod['precio']) * cantidad
                total += subtotal
                venta_items.append({
                    "codigo": codigo,
                    "nombre": prod['nombre'],
                    "cantidad": cantidad,
                    "precio": float(prod['precio']),
                    "subtotal": subtotal
                })
                prod['cantidad'] -= cantidad
            except (ValueError, KeyError, TypeError) as e:
                return jsonify({"success": False, "message": f"Error en producto {item.get('codigo')}: {str(e)}"}), 400

        save_data(user, 'inventario', productos_inv)

        ventas = load_data(user, 'ventas', [])
        venta = {
            "id": len(ventas) + 1,
            "fecha": now_iso(),
            "productos": venta_items,
            "total": float(total),
            "metodo_pago": data.get('metodo_pago', 'efectivo')
        }
        ventas.append(venta)
        save_data(user, 'ventas', ventas)

        # Registrar en caja
        caja = load_data(user, 'caja', {"movimientos": [], "cierres": []})
        caja["movimientos"].append({
            "id": len(caja["movimientos"]) + 1,
            "fecha": now_iso(),
            "tipo": "ingreso",
            "monto": float(total),
            "descripcion": f"Venta #{venta['id']}"
        })
        save_data(user, 'caja', caja)

        return jsonify({"success": True, "message": "Venta registrada", "venta": venta})
    
    except Exception as e:
        return jsonify({"success": False, "message": f"Error interno: {str(e)}"}), 500

# ==================== CAJA ====================
@app.route('/api/caja/estado', methods=['GET'])
def get_estado_caja():
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "No autorizado"}), 401
    ventas = load_data(user, 'ventas', [])
    caja = load_data(user, 'caja', {"movimientos": [], "cierres": []})

    hoy = today_iso()
    ventas_hoy = sum(v["total"] for v in ventas if v["fecha"].startswith(hoy))
    ingresos = sum(m["monto"] for m in caja["movimientos"] if m["tipo"] == "ingreso" and m["fecha"].startswith(hoy))
    egresos = sum(m["monto"] for m in caja["movimientos"] if m["tipo"] == "egreso" and m["fecha"].startswith(hoy))

    return jsonify({
        "fecha": hoy,
        "ventas_del_dia": ventas_hoy,
        "ingresos": ingresos,
        "egresos": egresos,
        "balance": ingresos - egresos
    })

@app.route('/api/caja/cierre-diario', methods=['POST'])
def cierre_diario():
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "No autorizado"}), 401
    caja = load_data(user, 'caja', {"movimientos": [], "cierres": []})
    ventas = load_data(user, 'ventas', [])

    hoy = today_iso()
    ventas_hoy = sum(v["total"] for v in ventas if v["fecha"].startswith(hoy))
    gastos = sum(m["monto"] for m in caja["movimientos"] if m["tipo"] == "egreso" and m["fecha"].startswith(hoy))

    cierre = {
        "id": len(caja["cierres"]) + 1,
        "tipo": "diario",
        "fecha": now_iso(),
        "ventas": ventas_hoy,
        "gastos": gastos,
        "total": ventas_hoy - gastos,
        "estado": "cerrado"
    }
    caja["cierres"].append(cierre)
    save_data(user, 'caja', caja)

    return jsonify({"success": True, "cierre": cierre})

@app.route('/api/caja/cierre-mensual', methods=['POST'])
def cierre_mensual():
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "No autorizado"}), 401
    data = request.json
    year = data.get('año', date.today().year)
    month = data.get('mes', date.today().month)

    caja = load_data(user, 'caja', {"movimientos": [], "cierres": []})
    ventas = load_data(user, 'ventas', [])

    ventas_mes = sum(v["total"] for v in filter_sales_by_date(ventas, year=year, month=month))

    cierre = {
        "id": len(caja["cierres"]) + 1,
        "tipo": "mensual",
        "fecha": now_iso(),
        "periodo": f"{year}-{month:02d}",
        "ventas": ventas_mes,
        "gastos": 0,  # Simplificado
        "total": ventas_mes,
        "estado": "cerrado"
    }
    caja["cierres"].append(cierre)
    save_data(user, 'caja', caja)

    return jsonify({"success": True, "cierre": cierre})

@app.route('/api/caja/cierres', methods=['GET'])
def get_cierres():
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "No autorizado"}), 401
    caja = load_data(user, 'caja', {"movimientos": [], "cierres": []})
    return jsonify(caja["cierres"])

# ==================== AUTENTICACIÓN ====================
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({"success": False, "message": "Usuario y contraseña requeridos"}), 400

    usuarios = load_global_data('usuarios', {})
    if username not in usuarios or usuarios[username]['password'] != password:
        return jsonify({"success": False, "message": "Credenciales incorrectas"}), 401

    token = secrets.token_hex(16)
    active_sessions[token] = {
        "username": username,
        "rol": usuarios[username].get('rol', 'usuario'),
        "login_time": now_iso()
    }

    return jsonify({
        "success": True,
        "message": "Login exitoso",
        "token": token,
        "user": {"username": username, "rol": active_sessions[token]["rol"]}
    })

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    rol = data.get('rol', 'usuario')

    if not username or not password:
        return jsonify({"success": False, "message": "Usuario y contraseña requeridos"}), 400

    if len(password) < 4:
        return jsonify({"success": False, "message": "La contraseña debe tener al menos 4 caracteres"}), 400

    usuarios = load_global_data('usuarios', {})
    if username in usuarios:
        return jsonify({"success": False, "message": "El usuario ya existe"}), 400

    usuarios[username] = {
        "password": password,
        "rol": rol,
        "fecha_creacion": now_iso()
    }
    save_global_data('usuarios', usuarios)

    return jsonify({"success": True, "message": "Usuario creado exitosamente"})

@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({"success": False, "message": "Usuario y nueva contraseña requeridos"}), 400

    if len(password) < 4:
        return jsonify({"success": False, "message": "La contraseña debe tener al menos 4 caracteres"}), 400

    usuarios = load_global_data('usuarios', {})
    if username not in usuarios:
        return jsonify({"success": False, "message": "Usuario no encontrado"}), 404

    usuarios[username]['password'] = password
    usuarios[username]['fecha_actualizacion'] = now_iso()
    save_global_data('usuarios', usuarios)

    return jsonify({"success": True, "message": "Contraseña restablecida con éxito"})

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    data = request.json
    token = data.get('token', '')
    if token in active_sessions:
        del active_sessions[token]
    return jsonify({"success": True, "message": "Sesión cerrada"})

@app.route('/api/auth/verify', methods=['GET'])
def verify_token():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token in active_sessions:
        return jsonify({"valid": True, "user": active_sessions[token]})
    return jsonify({"valid": False}), 401

@app.route('/api/auth/usuarios', methods=['GET'])
def get_usuarios():
    usuarios = load_global_data('usuarios', {})
    return jsonify({u: {"rol": data.get('rol'), "fecha_creacion": data.get('fecha_creacion')}
                   for u, data in usuarios.items()})

@app.route('/api/auth/usuarios/<username>', methods=['DELETE'])
def delete_usuario(username):
    usuarios = load_global_data('usuarios', {})
    if username not in usuarios:
        return jsonify({"success": False, "message": "Usuario no encontrado"}), 404
    del usuarios[username]
    save_global_data('usuarios', usuarios)
    return jsonify({"success": True, "message": "Usuario eliminado"})

# ==================== MAIN ====================

if __name__ == '__main__':
    import os
    # Render asigna un puerto dinámico a través de la variable de entorno PORT
    port = int(os.environ.get("PORT", 8080))
    # Corremos la app listos para producción, escuchando en todas las interfaces (0.0.0.0)
    app.run(host='0.0.0.0', port=port)
