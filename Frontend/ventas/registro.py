"""
Registro de Ventas
==================
Módulo para gestionar el registro de ventas.
"""

import json
from datetime import datetime, date
from typing import List, Optional
from pathlib import Path

# ==================== RUTAS ====================
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
SALES_FILE = DATA_DIR / "ventas.json"


# ==================== CLASE REGISTRO VENTAS ====================
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
    
    def registrar_ventas(self, productos: List[dict], total: float, 
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