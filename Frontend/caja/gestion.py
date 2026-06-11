"""
Gestión de Caja
===============
Módulo para administrar caja, cierres diarios y mensuales.
"""

import json
from datetime import datetime, date
from typing import List, Optional
from pathlib import Path

# ==================== RUTAS ====================
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
CASH_FILE = DATA_DIR / "caja.json"


# ==================== CLASE GESTIÓN CAJA ====================
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
            "tipo": tipo,
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
    
    def movimientos_del_dia(self, fecha: date = None) -> List[dict]:
        """Obtiene los movimientos del día."""
        if fecha is None:
            fecha = date.today()
        
        return [m for m in self.movimientos 
                if datetime.fromisoformat(m["fecha"]).date() == fecha]