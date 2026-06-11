"""
Gestión de Inventario
=====================
Módulo para administrar productos, stock y alertas.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# ==================== RUTAS ====================
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
INVENTORY_FILE = DATA_DIR / "inventario.json"


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
                         cantidad: int, umbral_minimo: int = 10) -> tuple:
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