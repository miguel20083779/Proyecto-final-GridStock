"""
Sistema de Gestión de Inventarios y Ventas
==========================================
Aplicación principal que integra los módulos.
"""

import sys

from pathlib import Path

# Agregar rutas de importación

sys.path.insert(0, str(Path(__file__).parent))

# Definición de archivos de datos
INVENTORY_FILE = Path(__file__).parent / 'inventario.json'
SALES_FILE = Path(__file__).parent / 'ventas.json'
CASH_FILE = Path(__file__).parent / 'caja.json'


from datetime import datetime, date
from typing import Optional, Dict, List
from inventario.producto import Inventario
from ventas.registro import RegistroVentas
from caja.gestion import GestionCaja


# ==================== CLASE INVENTARIO ====================
class Inventario:
    """Gestión de productos del inventario."""
    
    def __init__(self):
        self.productos: Dict[str, dict] = {}
        self.cargar()
    
    def cargar(self):
        """Carga el inventario desde el archivo JSON."""
        if INVENTORY_FILE.exists():
            with open(INVENTORY_FILE, 'r', encoding='utf-8') as f:
                self.productos = json.load(f)
    
    def guardar(self):
        """Guarda el inventario en el archivo JSON."""
        with open(INVENTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.productos, f, indent=4, ensure_ascii=False)
    
    def agregar_producto(self, codigo: str, nombre: str, precio: float, 
                         cantidad: int, umbral_minimo: int = 10):
        """Agrega un nuevo producto al inventario."""
        if codigo in self.productos:
            return False, "El producto ya existe"
        
        self.productos[codigo] = {
            "nombre": nombre,
            "precio": precio,
            "cantidad": cantidad,
            "umbral_minimo": umbral_minimo,
            "fecha_actualizacion": datetime.now().isoformat()
        }
        self.guardar()
        return True, "Producto agregado correctamente"
    
    def actualizar_producto(self, codigo: str, **kwargs) -> tuple:
        """Actualiza los datos de un producto."""
        if codigo not in self.productos:
            return False, "Producto no encontrado"
        
        for key, value in kwargs.items():
            if key in self.productos[codigo]:
                self.productos[codigo][key] = value
        
        self.productos[codigo]["fecha_actualizacion"] = datetime.now().isoformat()
        self.guardar()
        return True, "Producto actualizado correctamente"
    
    def eliminar_producto(self, codigo: str) -> tuple:
        """Elimina un producto del inventario."""
        if codigo not in self.productos:
            return False, "Producto no encontrado"
        
        del self.productos[codigo]
        self.guardar()
        return True, "Producto eliminado correctamente"
    
    def buscar_producto(self, codigo: str) -> Optional[dict]:
        """Busca un producto por código."""
        return self.productos.get(codigo)
    
    def listar_productos(self) -> Dict[str, dict]:
        """Lista todos los productos."""
        return self.productos
    
    def obtener_alertas(self) -> List[dict]:
        """Obtiene productos con stock bajo el umbral mínimo."""
        alertas = []
        for codigo, producto in self.productos.items():
            if producto["cantidad"] <= producto["umbral_minimo"]:
                alertas.append({
                    "codigo": codigo,
                    "nombre": producto["nombre"],
                    "cantidad": producto["cantidad"],
                    "umbral_minimo": producto["umbral_minimo"],
                    "necesario": producto["umbral_minimo"] - producto["cantidad"] + 5
                })
        return alertas
    
    def reducir_stock(self, codigo: str, cantidad: int) -> tuple:
        """Reduce el stock de un producto tras una venta."""
        if codigo not in self.productos:
            return False, "Producto no encontrado"
        
        if self.productos[codigo]["cantidad"] < cantidad:
            return False, f"Stock insuficiente. Disponible: {self.productos[codigo]['cantidad']}"
        
        self.productos[codigo]["cantidad"] -= cantidad
        self.productos[codigo]["fecha_actualizacion"] = datetime.now().isoformat()
        self.guardar()
        return True, "Stock reducido correctamente"


# ==================== CLASE VENTAS ====================
class RegistroVentas:
    """Gestión del registro de ventas."""
    
    def __init__(self):
        self.ventas: List[dict] = []
        self.cargar()
    
    def cargar(self):
        """Carga las ventas desde el archivo JSON."""
        if SALES_FILE.exists():
            with open(SALES_FILE, 'r', encoding='utf-8') as f:
                self.ventas = json.load(f)
    
    def guardar(self):
        """Guarda las ventas en el archivo JSON."""
        with open(SALES_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.ventas, f, indent=4, ensure_ascii=False)
    
    def registrar_venta(self, productos: List[dict], total: float, 
                        metodo_pago: str = "efectivo") -> dict:
        """Registra una nueva venta."""
        venta = {
            "id": len(self.ventas) + 1,
            "fecha": datetime.now().isoformat(),
            "productos": productos,
            "total": total,
            "metodo_pago": metodo_pago
        }
        self.ventas.append(venta)
        self.guardar()
        return venta
    
    def ventas_del_dia(self, fecha: date = None) -> List[dict]:
        """Obtiene las ventas del día especificado."""
        if fecha is None:
            fecha = date.today()
        
        ventas_dia = []
        for venta in self.ventas:
            venta_fecha = datetime.fromisoformat(venta["fecha"]).date()
            if venta_fecha == fecha:
                ventas_dia.append(venta)
        return ventas_dia
    
    def ventas_del_mes(self, año: int = None, mes: int = None) -> List[dict]:
        """Obtiene las ventas del mes especificado."""
        if año is None:
            año = date.today().year
        if mes is None:
            mes = date.today().month
        
        ventas_mes = []
        for venta in self.ventas:
            venta_fecha = datetime.fromisoformat(venta["fecha"])
            if venta_fecha.year == año and venta_fecha.month == mes:
                ventas_mes.append(venta)
        return ventas_mes
    
    def total_ventas_dia(self, fecha: date = None) -> float:
        """Calcula el total de ventas del día."""
        return sum(v["total"] for v in self.ventas_del_dia(fecha))
    
    def total_ventas_mes(self, año: int = None, mes: int = None) -> float:
        """Calcula el total de ventas del mes."""
        return sum(v["total"] for v in self.ventas_del_mes(año, mes))
    
    def listar_ventas(self) -> List[dict]:
        """Lista todas las ventas."""
        return self.ventas


# ==================== CLASE CAJA ====================
class GestionCaja:
    """Gestión de caja y cierres."""
    
    def __init__(self):
        self.movimientos: List[dict] = []
        self.cierres: List[dict] = []
        self.cargar()
    
    def cargar(self):
        """Carga los datos de caja desde el archivo JSON."""
        if CASH_FILE.exists():
            with open(CASH_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.movimientos = data.get("movimientos", [])
                self.cierres = data.get("cierres", [])
    
    def guardar(self):
        """Guarda los datos de caja en el archivo JSON."""
        with open(CASH_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "movimientos": self.movimientos,
                "cierres": self.cierres
            }, f, indent=4, ensure_ascii=False)
    
    def registrar_movimiento(self, tipo: str, monto: float, 
                             descripcion: str = "") -> dict:
        """Registra un movimiento de caja (ingreso/egreso)."""
        movimiento = {
            "id": len(self.movimientos) + 1,
            "fecha": datetime.now().isoformat(),
            "tipo": tipo,  # "ingreso" o "egreso"
            "monto": monto,
            "descripcion": descripcion
        }
        self.movimientos.append(movimiento)
        self.guardar()
        return movimiento
    
    def cierre_diario(self, ventas_del_dia: float, gastos: float = 0) -> dict:
        """Realiza el cierre de caja del día."""
        cierre = {
            "id": len(self.cierres) + 1,
            "tipo": "diario",
            "fecha": datetime.now().isoformat(),
            "ventas": ventas_del_dia,
            "gastos": gastos,
            "total": ventas_del_dia - gastos,
            "estado": "cerrado"
        }
        self.cierres.append(cierre)
        self.guardar()
        return cierre
    
    def cierre_mensual(self, año: int, mes: int, ventas_del_mes: float, 
                       gastos: float = 0) -> dict:
        """Realiza el cierre de caja del mes."""
        cierre = {
            "id": len(self.cierres) + 1,
            "tipo": "mensual",
            "fecha": datetime.now().isoformat(),
            "periodo": f"{año}-{mes:02d}",
            "ventas": ventas_del_mes,
            "gastos": gastos,
            "total": ventas_del_mes - gastos,
            "estado": "cerrado"
        }
        self.cierres.append(cierre)
        self.guardar()
        return cierre
    
    def obtener_cierre_dia(self, fecha: date = None) -> Optional[dict]:
        """Obtiene el cierre de caja de un día específico."""
        if fecha is None:
            fecha = date.today()
        
        for cierre in self.cierres:
            if cierre["tipo"] == "diario":
                cierre_fecha = datetime.fromisoformat(cierre["fecha"]).date()
                if cierre_fecha == fecha:
                    return cierre
        return None
    
    def obtener_cierre_mes(self, año: int, mes: int) -> Optional[dict]:
        """Obtiene el cierre de caja de un mes específico."""
        for cierre in self.cierres:
            if cierre["tipo"] == "mensual" and cierre.get("periodo") == f"{año}-{mes:02d}":
                return cierre
        return None
    
    def listar_cierres(self) -> List[dict]:
        """Lista todos los cierres de caja."""
        return self.cierres


# ==================== CLASE PRINCIPAL APP ====================
class AppInventario:
    """Aplicación principal de gestión."""
    
    def __init__(self):
        self.inventario = Inventario()
        self.ventas = RegistroVentas()
        self.caja = GestionCaja()
    
    # --- Métodos de Inventario ---
    def agregar_producto(self, codigo: str, nombre: str, precio: float, 
                         cantidad: int, umbral: int = 10):
        return self.inventario.agregar_producto(codigo, nombre, precio, cantidad, umbral)
    
    def buscar_producto(self, codigo: str):
        return self.inventario.buscar_producto(codigo)
    
    def listar_inventario(self):
        return self.inventario.listar_productos()
    
    def obtener_alertas(self):
        return self.inventario.obtener_alertas()
    
    # --- Métodos de Ventas ---
    def realizar_venta(self, items: List[dict], metodo_pago: str = "efectivo"):
        """Procesa una venta completa."""
        productos_venta = []
        total = 0
        
        for item in items:
            codigo = item["codigo"]
            cantidad = item["cantidad"]
            
            producto = self.inventario.buscar_producto(codigo)
            if not producto:
                return False, f"Producto {codigo} no encontrado"
            
            if producto["cantidad"] < cantidad:
                return False, f"Stock insuficiente para {producto['nombre']}"
            
            subtotal = producto["precio"] * cantidad
            total += subtotal
            
            productos_venta.append({
                "codigo": codigo,
                "nombre": producto["nombre"],
                "cantidad": cantidad,
                "precio": producto["precio"],
                "subtotal": subtotal
            })
            
            # Reducir stock
            self.inventario.reducir_stock(codigo, cantidad)
        
        # Registrar venta
        self.ventas.registrar_ventas(productos_venta, total, metodo_pago)
        
        # Registrar ingreso en caja
        self.caja.registrar_movimiento("ingreso", total, "Venta registrada")
        
        return True, f"Venta registrada por ${total:.2f}"
    
    def ventas_hoy(self):
        return self.ventas.ventas_del_dia()
    
    def ventas_mes_actual(self):
        hoy = date.today()
        return self.ventas.ventas_del_mes(hoy.year, hoy.month)
    
    # --- Métodos de Caja ---
    def cierre_caja_dia(self):
        """Realiza el cierre de caja del día."""
        ventas_hoy = self.ventas.total_ventas_dia()
        return self.caja.cierre_diario(ventas_hoy)
    
    def cierre_caja_mes(self, año: int = None, mes: int = None):
        """Realiza el cierre de caja del mes."""
        if año is None:
            hoy = date.today()
            año, mes = hoy.year, hoy.month
        
        ventas_mes = self.ventas.total_ventas_mes(año, mes)
        return self.caja.cierre_mensual(año, mes, ventas_mes)
    
    def estado_caja_actual(self):
        """Muestra el estado actual de la caja."""
        hoy = date.today()
        ventas_hoy = self.ventas.total_ventas_dia(hoy)
        
        ingresos = sum(m["monto"] for m in self.caja.movimientos 
                      if m["tipo"] == "ingreso" and 
                      datetime.fromisoformat(m["fecha"]).date() == hoy)
        
        egresos = sum(m["monto"] for m in self.caja.movimientos 
                     if m["tipo"] == "egreso" and 
                     datetime.fromisoformat(m["fecha"]).date() == hoy)
        
        return {
            "fecha": hoy.isoformat(),
            "ventas_del_dia": ventas_hoy,
            "ingresos": ingresos,
            "egresos": egresos,
            "balance": ingresos - egresos
        }


# ==================== INTERFAZ DE CONSOLA ====================
def menu_principal():
    """Muestra el menú principal de la aplicación."""
    app = AppInventario()
    
    while True:
        print("\n" + "="*50)
        print("   SISTEMA DE GESTIÓN DE INVENTARIOS Y VENTAS")
        print("="*50)
        print("1. 📦 Gestión de Inventario")
        print("2. 🛒 Registrar Venta")
        print("3. 📊 Reportes de Ventas")
        print("4. 💰 Cierre de Caja")
        print("5. ⚠️  Alertas de Stock")
        print("6. 🚪 Salir")
        print("="*50)
        
        opcion = input("\nSeleccione una opción: ").strip()
        
        if opcion == "1":
            menu_inventario(app)
        elif opcion == "2":
            menu_ventas(app)
        elif opcion == "3":
            menu_reportes(app)
        elif opcion == "4":
            menu_cierre_caja(app)
        elif opcion == "5":
            mostrar_alertas(app)
        elif opcion == "6":
            print("\n¡Gracias por usar el sistema!")
            break
        else:
            print("\n❌ Opción inválida")


def menu_inventario(app: AppInventario):
    """Menú de gestión de inventario."""
    while True:
        print("\n--- GESTIÓN DE INVENTARIO ---")
        print("1. Agregar producto")
        print("2. Buscar producto")
        print("3. Listar inventario")
        print("4. Actualizar producto")
        print("5. Eliminar producto")
        print("6. Volver al menú principal")
        
        opcion = input("\nSeleccione: ").strip()
        
        if opcion == "1":
            print("\n--- AGREGAR PRODUCTO ---")
            codigo = input("Código: ").strip()
            nombre = input("Nombre: ").strip()
            try:
                precio = float(input("Precio: "))
                cantidad = int(input("Cantidad: "))
                umbral = int(input("Umbral mínimo (default 10): ") or "10")
                ok, msg = app.agregar_producto(codigo, nombre, precio, cantidad, umbral)
                print(f"\n{'✅' if ok else '❌'} {msg}")
            except ValueError:
                print("\n❌ Error: Ingrese valores numéricos válidos")
        
        elif opcion == "2":
            codigo = input("\nCódigo del producto: ").strip()
            producto = app.buscar_producto(codigo)
            if producto:
                print(f"\n📦 Producto: {producto['nombre']}")
                print(f"   Precio: ${producto['precio']:.2f}")
                print(f"   Stock: {producto['cantidad']}")
                print(f"   Umbral mínimo: {producto['umbral_minimo']}")
            else:
                print("\n❌ Producto no encontrado")
        
        elif opcion == "3":
            productos = app.listar_inventario()
            if productos:
                print("\n--- INVENTARIO ACTUAL ---")
                print(f"{'Código':<10} {'Nombre':<20} {'Precio':<10} {'Stock':<8} {'Umbral':<8}")
                print("-" * 60)
                for cod, prod in productos.items():
                    print(f"{cod:<10} {prod['nombre']:<20} ${prod['precio']:<9.2f} {prod['cantidad']:<8} {prod['umbral_minimo']:<8}")
            else:
                print("\n📭 El inventario está vacío")
        
        elif opcion == "4":
            codigo = input("\nCódigo del producto: ").strip()
            producto = app.buscar_producto(codigo)
            if producto:
                print(f"Actualizando: {producto['nombre']}")
                try:
                    nombre = input(f"Nombre [{producto['nombre']}]: ").strip()
                    precio = input(f"Precio [{producto['precio']}]: ").strip()
                    cantidad = input(f"Cantidad [{producto['cantidad']}]: ").strip()
                    umbral = input(f"Umbral [{producto['umbral_minimo']}]: ").strip()
                    
                    kwargs = {}
                    if nombre: kwargs["nombre"] = nombre
                    if precio: kwargs["precio"] = float(precio)
                    if cantidad: kwargs["cantidad"] = int(cantidad)
                    if umbral: kwargs["umbral_minimo"] = int(umbral)
                    
                    if kwargs:
                        ok, msg = app.inventario.actualizar_producto(codigo, **kwargs)
                        print(f"\n{'✅' if ok else '❌'} {msg}")
                except ValueError:
                    print("\n❌ Error: Valores numéricos inválidos")
            else:
                print("\n❌ Producto no encontrado")
        
        elif opcion == "5":
            codigo = input("\nCódigo del producto a eliminar: ").strip()
            ok, msg = app.inventario.eliminar_producto(codigo)
            print(f"\n{'✅' if ok else '❌'} {msg}")
        
        elif opcion == "6":
            break


def menu_ventas(app: AppInventario):
    """Menú de registro de ventas."""
    print("\n--- REGISTRAR VENTA ---")
    
    items = []
    while True:
        print("\nAgregar producto a la venta:")
        codigo = input("Código (o 'fin' para terminar): ").strip()
        
        if codigo.lower() == "fin":
            break
        
        producto = app.buscar_producto(codigo)
        if not producto:
            print("❌ Producto no encontrado")
            continue
        
        try:
            cantidad = int(input(f"Cantidad (disponible: {producto['cantidad']}): "))
            if cantidad <= 0:
                print("❌ Cantidad inválida")
                continue
            if cantidad > producto["cantidad"]:
                print(f"❌ Stock insuficiente. Disponible: {producto['cantidad']}")
                continue
        except ValueError:
            print("❌ Cantidad inválida")
            continue
        
        items.append({"codigo": codigo, "cantidad": cantidad})
        print(f"✅ Agregado: {producto['nombre']} x{cantidad}")
    
    if items:
        print("\n--- RESUMEN DE VENTA ---")
        total = 0
        for item in items:
            prod = app.buscar_producto(item["codigo"])
            subtotal = prod["precio"] * item["cantidad"]
            total += subtotal
            print(f"  {prod['nombre']} x{item['cantidad']} = ${subtotal:.2f}")
        print(f"\nTOTAL: ${total:.2f}")
        
        confirmar = input("\n¿Confirmar venta? (s/n): ").strip().lower()
        if confirmar == "s":
            metodo = input("Método de pago (efectivo/tarjeta): ").strip() or "efectivo"
            ok, msg = app.realizar_venta(items, metodo)
            print(f"\n{'✅' if ok else '❌'} {msg}")
    else:
        print("\nNo se agregaron productos")


def menu_reportes(app: AppInventario):
    """Menú de reportes de ventas."""
    while True:
        print("\n--- REPORTES DE VENTAS ---")
        print("1. Ventas de hoy")
        print("2. Ventas del mes")
        print("3. Todas las ventas")
        print("4. Volver")
        
        opcion = input("\nSeleccione: ").strip()
        
        if opcion == "1":
            ventas = app.ventas_hoy()
            print(f"\n--- VENTAS DE HOY ({date.today().isoformat()}) ---")
            if ventas:
                total = 0
                for v in ventas:
                    print(f"  #{v['id']} - ${v['total']:.2f} - {v['metodo_pago']}")
                    total += v['total']
                print(f"\nTotal: ${total:.2f}")
            else:
                print("No hay ventas hoy")
        
        elif opcion == "2":
            ventas = app.ventas_mes_actual()
            hoy = date.today()
            print(f"\n--- VENTAS DE {hoy.strftime('%B %Y').upper()} ---")
            if ventas:
                total = 0
                for v in ventas:
                    fecha = datetime.fromisoformat(v['fecha']).strftime('%d/%m %H:%M')
                    print(f"  #{v['id']} - {fecha} - ${v['total']:.2f}")
                    total += v['total']
                print(f"\nTotal del mes: ${total:.2f}")
            else:
                print("No hay ventas este mes")
        
        elif opcion == "3":
            ventas = app.ventas.listar_ventas()
            print(f"\n--- TODAS LAS VENTAS ({len(ventas)} ventas) ---")
            if ventas:
                for v in ventas[-10:]:  # Últimas 10
                    fecha = datetime.fromisoformat(v['fecha']).strftime('%d/%m/%Y %H:%M')
                    print(f"  #{v['id']} - {fecha} - ${v['total']:.2f}")
        
        elif opcion == "4":
            break


def menu_cierre_caja(app: AppInventario):
    """Menú de cierre de caja."""
    while True:
        print("\n--- CIERRE DE CAJA ---")
        print("1. Estado de caja actual")
        print("2. Cierre de caja del día")
        print("3. Cierre de caja del mes")
        print("4. Ver cierres anteriores")
        print("5. Volver")
        
        opcion = input("\nSeleccione: ").strip()
        
        if opcion == "1":
            estado = app.estado_caja_actual()
            print(f"\n--- CAJA DEL DÍA {estado['fecha']} ---")
            print(f"  Ventas del día: ${estado['ventas_del_dia']:.2f}")
            print(f"  Ingresos: ${estado['ingresos']:.2f}")
            print(f"  Egresos: ${estado['egresos']:.2f}")
            print(f"  Balance: ${estado['balance']:.2f}")
        
        elif opcion == "2":
            cierre = app.cierre_caja_dia()
            print(f"\n--- CIERRE DE CAJA DIARIO ---")
            print(f"  Fecha: {datetime.fromisoformat(cierre['fecha']).strftime('%d/%m/%Y %H:%M')}")
            print(f"  Ventas: ${cierre['ventas']:.2f}")
            print(f"  Gastos: ${cierre['gastos']:.2f}")
            print(f"  Total: ${cierre['total']:.2f}")
            print(f"  Estado: {cierre['estado'].upper()}")
        
        elif opcion == "3":
            hoy = date.today()
            cierre = app.cierre_caja_mes(hoy.year, hoy.month)
            print(f"\n--- CIERRE DE CAJA MENSUAL ---")
            print(f"  Período: {hoy.strftime('%B %Y').upper()}")
            print(f"  Ventas: ${cierre['ventas']:.2f}")
            print(f"  Gastos: ${cierre['gastos']:.2f}")
            print(f"  Total: ${cierre['total']:.2f}")
            print(f"  Estado: {cierre['estado'].upper()}")
        
        elif opcion == "4":
            cierres = app.caja.listar_cierres()
            print("\n--- CIERRES ANTERIORES ---")
            if cierres:
                for c in cierres[-10:]:
                    fecha = datetime.fromisoformat(c['fecha']).strftime('%d/%m/%Y %H:%M')
                    periodo = c.get('periodo', fecha[:10])
                    print(f"  #{c['id']} - {c['tipo'].upper()} {periodo} - ${c['total']:.2f}")
            else:
                print("No hay cierres registrados")
        
        elif opcion == "5":
            break


def mostrar_alertas(app: AppInventario):
    """Muestra las alertas de stock bajo mínimo."""
    alertas = app.obtener_alertas()
    
    print("\n" + "="*50)
    print("   ⚠️  ALERTAS DE STOCK BAJO")
    print("="*50)
    
    if alertas:
        print(f"\n{'Código':<10} {'Producto':<20} {'Stock':<8} {'Mínimo':<8} {'Sugerido':<10}")
        print("-" * 60)
        for a in alertas:
            print(f"{a['codigo']:<10} {a['nombre']:<20} {a['cantidad']:<8} {a['umbral_minimo']:<8} {a['necesario']:<10}")
        print(f"\n⚠️  {len(alertas)} producto(s) requieren reposición")
    else:
        print("\n✅ No hay alertas de stock. Todos los productos tienen stock adecuado.")


# ==================== PUNTO DE ENTRADA ====================
if __name__ == "__main__":
    print("\n" + "="*50)
    print("   BIENVENIDO AL SISTEMA DE GESTIÓN")
    print("="*50)
    menu_principal()