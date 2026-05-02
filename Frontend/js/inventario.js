// Lógica de inventario para el frontend
const API_URL = "http://localhost:8000";

export function cargarProductos(tabla) {
    fetch(`${API_URL}/productos`)
        .then(res => res.json())
        .then(productos => {
            tabla.innerHTML = "";
            productos.forEach(p => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${p.codigo}</td>
                    <td>${p.nombre}</td>
                    <td>${p.precio}</td>
                    <td>${p.cantidad}</td>
                    <td>${p.umbral_minimo}</td>
                    <td><button onclick="eliminarProducto('${p.codigo}')">Eliminar</button></td>
                `;
                tabla.appendChild(tr);
            });
        });
}

export function agregarProducto(producto, callback) {
    fetch(`${API_URL}/productos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(producto)
    })
    .then(res => {
        if (!res.ok) throw new Error("Error al agregar producto");
        return res.json();
    })
    .then(callback)
    .catch(alert);
}

window.eliminarProducto = function(codigo) {
    fetch(`${API_URL}/productos/${codigo}`, { method: "DELETE" })
        .then(res => {
            if (!res.ok) throw new Error("Error al eliminar producto");
            location.reload();
        })
        .catch(alert);
}
