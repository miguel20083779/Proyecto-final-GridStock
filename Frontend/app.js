// Configuración
const API_URL = 'http://localhost:5000/api';

// Verificar autenticación
const token = localStorage.getItem('gridstock_token');
if (!token) {
    window.location.href = 'login.html';
}

// Función para hacer peticiones autenticadas
async function authFetch(url, options = {}) {
    const token = localStorage.getItem('gridstock_token');
    options.headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`
    };
    const response = await fetch(url, options);
    if (response.status === 401) {
        localStorage.removeItem('gridstock_token');
        localStorage.removeItem('gridstock_user');
        window.location.href = 'login.html';
    }
    return response;
}

// Carrito de ventas
let carrito = [];

// ==================== NAVEGACIÓN ====================
document.addEventListener('DOMContentLoaded', () => {
    // Mostrar usuario logueado
    const user = JSON.parse(localStorage.getItem('gridstock_user') || '{}');
    if (user.username) {
        const userDisplay = document.createElement('div');
        userDisplay.className = 'user-info';
        userDisplay.innerHTML = `<span>👤 ${user.username}</span> <button onclick="logout()">Cerrar Sesión</button>`;
        document.querySelector('.sidebar').appendChild(userDisplay);
    }
    
    // Navegación del sidebar
    document.querySelectorAll('.sidebar nav a').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = link.dataset.page;
            showPage(page);
            
            // Actualizar clase active
            document.querySelectorAll('.sidebar nav a').forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        });
    });

    // Tabs en reportes
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            cargarVentas(tab.dataset.tab);
        });
    });

    // Formulario agregar producto
    document.getElementById('form-agregar-producto').addEventListener('submit', agregarProducto);

    // Cargar datos iniciales
    cargarInventario();
    cargarAlertas();
    cargarEstadoCaja();
    cargarVentas('hoy');
});

function showPage(pageId) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');

    // Actualizar datos según la página
    if (pageId === 'inventario') cargarInventario();
    if (pageId === 'ventas') cargarProductosVenta();
    if (pageId === 'reportes') {
        cargarVentas('hoy');
        cargarStatsVentas();
    }
    if (pageId === 'caja') {
        cargarEstadoCaja();
        cargarCierres();
    }
    if (pageId === 'alertas') cargarAlertas();
}


// ==================== INVENTARIO ====================
async function cargarInventario() {
    try {
        const response = await fetch(`${API_URL}/inventario`);
        const productos = await response.json();
        
        const tbody = document.querySelector('#tabla-inventario tbody');
        tbody.innerHTML = '';

        for (const [codigo, prod] of Object.entries(productos)) {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${codigo}</td>
                <td>${prod.nombre}</td>
                <td>$${parseFloat(prod.precio).toFixed(2)}</td>
                <td>${prod.cantidad}</td>
                <td>${prod.umbral_minimo}</td>
                <td class="action-btns">
                    <button class="btn-danger" onclick="eliminarProducto('${codigo}')">Eliminar</button>
                </td>
            `;
            tbody.appendChild(tr);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

async function agregarProducto(e) {
    e.preventDefault();
    
    const data = {
        codigo: document.getElementById('prod-codigo').value,
        nombre: document.getElementById('prod-nombre').value,
        precio: parseFloat(document.getElementById('prod-precio').value),
        cantidad: parseInt(document.getElementById('prod-cantidad').value),
        umbral_minimo: parseInt(document.getElementById('prod-umbral').value)
    };

    try {
        const response = await fetch(`${API_URL}/inventario`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        alert(result.message);
        
        if (result.success) {
            document.getElementById('form-agregar-producto').reset();
            cargarInventario();
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al agregar producto');
    }
}

async function eliminarProducto(codigo) {
    if (!confirm(`¿Eliminar producto ${codigo}?`)) return;

    try {
        const response = await fetch(`${API_URL}/inventario/${codigo}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        alert(result.message);
        cargarInventario();
    } catch (error) {
        console.error('Error:', error);
    }
}


// ==================== VENTAS ====================
async function cargarProductosVenta() {
    try {
        const response = await fetch(`${API_URL}/inventario`);
        const productos = await response.json();
        
        const select = document.getElementById('venta-producto');
        select.innerHTML = '<option value="">Seleccionar producto...</option>';

        for (const [codigo, prod] of Object.entries(productos)) {
            if (prod.cantidad > 0) {
                const option = document.createElement('option');
                option.value = codigo;
                option.textContent = `${codigo} - ${prod.nombre} (Stock: ${prod.cantidad}) - $${parseFloat(prod.precio).toFixed(2)}`;
                select.appendChild(option);
            }
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

function agregarItemVenta() {
    const select = document.getElementById('venta-producto');
    const cantidad = parseInt(document.getElementById('venta-cantidad').value);
    
    const codigo = select.value;
    if (!codigo) {
        alert('Seleccione un producto');
        return;
    }
    if (cantidad < 1) {
        alert('Cantidad inválida');
        return;
    }

    // Obtener datos del producto
    fetch(`${API_URL}/inventario/${codigo}`)
        .then(res => res.json())
        .then(prod => {
            if (prod.cantidad < cantidad) {
                alert(`Stock insuficiente. Disponible: ${prod.cantidad}`);
                return;
            }

            // Verificar si ya está en el carrito
            const existente = carrito.find(item => item.codigo === codigo);
            if (existente) {
                existente.cantidad += cantidad;
            } else {
                carrito.push({
                    codigo: codigo,
                    nombre: prod.nombre,
                    precio: prod.precio,
                    cantidad: cantidad
                });
            }

            actualizarCarrito();
        });
}

function actualizarCarrito() {
    const tbody = document.querySelector('#tabla-carrito tbody');
    tbody.innerHTML = '';
    
    let total = 0;
    
    carrito.forEach((item, index) => {
        const subtotal = item.precio * item.cantidad;
        total += subtotal;
        
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${item.nombre}</td>
            <td>${item.cantidad}</td>
            <td>$${parseFloat(item.precio).toFixed(2)}</td>
            <td>$${subtotal.toFixed(2)}</td>
            <td><button class="btn-danger" onclick="eliminarDelCarrito(${index})">X</button></td>
        `;
        tbody.appendChild(tr);
    });

    document.getElementById('total-venta').textContent = total.toFixed(2);
}

function eliminarDelCarrito(index) {
    carrito.splice(index, 1);
    actualizarCarrito();
}

async function finalizarVenta() {
    if (carrito.length === 0) {
        alert('El carrito está vacío');
        return;
    }

    const metodoPago = document.getElementById('metodo-pago').value;
    
    const data = {
        productos: carrito,
        metodo_pago: metodoPago
    };

    try {
        const response = await fetch(`${API_URL}/ventas`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`Venta registrada: $${result.venta.total.toFixed(2)}`);
            carrito = [];
            actualizarCarrito();
            cargarInventario();
            cargarAlertas();
        } else {
            alert(result.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al registrar venta');
    }
}


// ==================== REPORTES ====================
async function cargarStatsVentas() {
    try {
        const [resHoy, resMes] = await Promise.all([
            fetch(`${API_URL}/ventas/total-hoy`),
            fetch(`${API_URL}/ventas/total-mes`)
        ]);
        
        const dataHoy = await resHoy.json();
        const dataMes = await resMes.json();
        
        document.getElementById('ventas-hoy').textContent = `$${dataHoy.total.toFixed(2)}`;
        document.getElementById('ventas-mes').textContent = `$${dataMes.total.toFixed(2)}`;
    } catch (error) {
        console.error('Error:', error);
    }
}

async function cargarVentas(tipo) {
    let url = `${API_URL}/ventas`;
    
    if (tipo === 'hoy') {
        url = `${API_URL}/ventas/hoy`;
    } else if (tipo === 'mes') {
        url = `${API_URL}/ventas/mes`;
    }

    try {
        const response = await fetch(url);
        const ventas = await response.json();
        
        const tbody = document.querySelector('#tabla-ventas tbody');
        tbody.innerHTML = '';

        ventas.forEach(v => {
            const fecha = new Date(v.fecha).toLocaleString('es-ES');
            const productos = v.productos.map(p => `${p.nombre} x${p.cantidad}`).join(', ');
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>#${v.id}</td>
                <td>${fecha}</td>
                <td>${productos}</td>
                <td>$${v.total.toFixed(2)}</td>
                <td>${v.metodo_pago}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Error:', error);
    }
}


// ==================== CAJA ====================
async function cargarEstadoCaja() {
    try {
        const response = await fetch(`${API_URL}/caja/estado`);
        const estado = await response.json();
        
        document.getElementById('caja-ventas').textContent = `$${estado.ventas_del_dia.toFixed(2)}`;
        document.getElementById('caja-ingresos').textContent = `$${estado.ingresos.toFixed(2)}`;
        document.getElementById('caja-egresos').textContent = `$${estado.egresos.toFixed(2)}`;
        document.getElementById('caja-balance').textContent = `$${estado.balance.toFixed(2)}`;
    } catch (error) {
        console.error('Error:', error);
    }
}

async function cierreDiario() {
    if (!confirm('¿Realizar cierre de caja del día?')) return;

    try {
        const response = await fetch(`${API_URL}/caja/cierre-diario`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`Cierre diario realizado:\nVentas: $${result.cierre.ventas.toFixed(2)}\nTotal: $${result.cierre.total.toFixed(2)}`);
            cargarCierres();
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

async function cierreMensual() {
    if (!confirm('¿Realizar cierre de caja del mes?')) return;

    try {
        const response = await fetch(`${API_URL}/caja/cierre-mensual`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`Cierre mensual realizado:\nVentas: $${result.cierre.ventas.toFixed(2)}\nTotal: $${result.cierre.total.toFixed(2)}`);
            cargarCierres();
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

async function cargarCierres() {
    try {
        const response = await fetch(`${API_URL}/caja/cierres`);
        const cierres = await response.json();
        
        const tbody = document.querySelector('#tabla-cierres tbody');
        tbody.innerHTML = '';

        cierres.forEach(c => {
            const fecha = new Date(c.fecha).toLocaleString('es-ES');
            const periodo = c.periodo || c.fecha.split('T')[0];
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>#${c.id}</td>
                <td>${c.tipo}</td>
                <td>${periodo}</td>
                <td>$${c.ventas.toFixed(2)}</td>
                <td>$${c.total.toFixed(2)}</td>
                <td>${fecha}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Error:', error);
    }
}


// ==================== ALERTAS ====================
async function cargarAlertas() {
    try {
        const response = await fetch(`${API_URL}/inventario/alertas`);
        const alertas = await response.json();
        
        const tbody = document.querySelector('#tabla-alertas tbody');
        const sinAlertas = document.getElementById('sin-alertas');
        
        if (alertas.length === 0) {
            tbody.innerHTML = '';
            sinAlertas.style.display = 'block';
        } else {
            sinAlertas.style.display = 'none';
            
            tbody.innerHTML = '';
            alertas.forEach(a => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${a.codigo}</td>
                    <td>${a.nombre}</td>
                    <td>${a.cantidad}</td>
                    <td>${a.umbral_minimo}</td>
                    <td>${a.necesario}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (error) {
        console.error('Error:', error);
    }
}


// ==================== LOGOUT ====================
async function logout() {
    const token = localStorage.getItem('gridstock_token');
    
    try {
        await fetch(`${API_URL}/auth/logout`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token })
        });
    } catch (error) {
        console.error('Error:', error);
    }
    
    localStorage.removeItem('gridstock_token');
    localStorage.removeItem('gridstock_user');
    window.location.href = 'login.html';
}