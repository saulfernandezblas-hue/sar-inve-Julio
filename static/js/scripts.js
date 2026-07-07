/**
 * SAR-INVENTORY - Main JavaScript
 */

// Mobile Sidebar Toggle
document.addEventListener('DOMContentLoaded', () => {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('show');
        });
    }

    // Auto-update datetime in navbar
    const datetimeDisplay = document.getElementById('datetimeDisplay');
    if (datetimeDisplay) {
        setInterval(() => {
            const now = new Date();
            const options = { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute:'2-digit' };
            datetimeDisplay.textContent = now.toLocaleDateString('es-ES', options);
        }, 1000);
    }
});

// Utility to show Bootstrap Toasts
function showToast(message, type = 'success') {
    const container = document.querySelector('.toast-container');
    if (!container) return;

    let icon = 'fa-check-circle';
    let bsClass = 'success';
    
    if (type === 'error' || type === 'danger') {
        icon = 'fa-triangle-exclamation';
        bsClass = 'danger';
    } else if (type === 'warning') {
        icon = 'fa-circle-exclamation';
        bsClass = 'warning';
    }

    const toastHTML = `
        <div class="toast align-items-center text-bg-${bsClass} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body fw-medium">
                    <i class="fa-solid ${icon} me-2"></i> ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', toastHTML);
    const toastEl = container.lastElementChild;
    const bsToast = new bootstrap.Toast(toastEl, { delay: 5000 });
    bsToast.show();
    
    toastEl.addEventListener('hidden.bs.toast', () => {
        toastEl.remove();
    });
}

// ---------------------------------------------------------
// DASHBOARD LOGIC
// ---------------------------------------------------------
let stateChartInstance = null;
let categoryChartInstance = null;

function fetchDashboardStats() {
    fetch('/api/dashboard/stats')
        .then(response => {
            if (!response.ok) throw new Error('Error de red');
            return response.json();
        })
        .then(data => {
            // Update counters
            animateValue('stat-total', data.total_equipos);
            animateValue('stat-bueno', data.buenos.cantidad);
            animateValue('stat-regular', data.regulares.cantidad);
            animateValue('stat-malo', data.malos.cantidad);
            
            // Update percentages & progress bars
            document.getElementById('stat-bueno-pct').textContent = `${data.buenos.porcentaje}%`;
            document.getElementById('stat-regular-pct').textContent = `${data.regulares.porcentaje}%`;
            document.getElementById('stat-malo-pct').textContent = `${data.malos.porcentaje}%`;
            
            document.getElementById('stat-bueno-bar').style.width = `${data.buenos.porcentaje}%`;
            document.getElementById('stat-regular-bar').style.width = `${data.regulares.porcentaje}%`;
            document.getElementById('stat-malo-bar').style.width = `${data.malos.porcentaje}%`;
            
            // Render Alerts
            renderAlerts(data.alertas);
            
            // Render Movements
            renderMovimientos(data.ultimos_movimientos);
            
            // Render Charts
            renderCharts(data);
        })
        .catch(error => {
            console.error('Error fetching stats:', error);
            document.getElementById('alertas-container').innerHTML = '<div class="text-danger p-3"><i class="fa-solid fa-triangle-exclamation me-2"></i> Error al cargar los datos.</div>';
        });
}

function animateValue(id, end) {
    const obj = document.getElementById(id);
    if(!obj) return;
    let startTimestamp = null;
    const duration = 1000;
    
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        obj.innerHTML = Math.floor(progress * end);
        if (progress < 1) {
            window.requestAnimationFrame(step);
        } else {
            obj.innerHTML = end;
        }
    };
    window.requestAnimationFrame(step);
}

function renderAlerts(alertas) {
    const container = document.getElementById('alertas-container');
    if (!container) return;
    
    if (alertas.length === 0) {
        container.innerHTML = `
            <div class="text-center p-4 text-muted">
                <i class="fa-solid fa-shield-check fs-2 mb-2 text-success opacity-50"></i>
                <p class="mb-0">Todo en orden. No hay alertas críticas actuales.</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    alertas.forEach(a => {
        let isLowQuantity = a.cantidad < 3;
        let isBadState = a.estado === 'Malo';
        let bgClass = isBadState ? 'danger' : 'warning';
        let icon = isBadState ? 'fa-circle-xmark' : 'fa-battery-quarter';
        let reason = isBadState ? 'Estado Crítico' : 'Stock Bajo';
        
        html += `
            <div class="d-flex p-3 rounded-3 bg-${bgClass} bg-opacity-10 border border-${bgClass} border-opacity-25 clickable" onclick="window.location.href='/inventario?search=${a.codigo}'">
                <div class="me-3 mt-1 text-${bgClass}">
                    <i class="fa-solid ${icon} fs-4"></i>
                </div>
                <div>
                    <h6 class="mb-1 text-white fw-bold">${a.nombre} <span class="badge bg-${bgClass} ms-2">${reason}</span></h6>
                    <div class="small text-light">Código: <span class="font-monospace text-muted">${a.codigo}</span> | Cantidad actual: <strong class="${isLowQuantity ? 'text-warning' : ''}">${a.cantidad}</strong></div>
                </div>
            </div>
        `;
    });
    container.innerHTML = html;
}

function renderMovimientos(movimientos) {
    const tbody = document.getElementById('movimientos-table');
    if (!tbody) return;
    
    if (movimientos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">No hay movimientos registrados.</td></tr>';
        return;
    }
    
    let html = '';
    movimientos.forEach(m => {
        let actionBadge = '';
        if (m.accion === 'Agregó') actionBadge = '<span class="badge bg-success bg-opacity-25 text-success"><i class="fa-solid fa-plus me-1"></i> Agregó</span>';
        else if (m.accion === 'Modificó') actionBadge = '<span class="badge bg-warning bg-opacity-25 text-warning"><i class="fa-solid fa-pencil me-1"></i> Modificó</span>';
        else actionBadge = '<span class="badge bg-danger bg-opacity-25 text-danger"><i class="fa-solid fa-trash me-1"></i> Eliminó</span>';
        
        // Usar fecha ya formateada del backend (dd/mm/YYYY HH:MM)
        const fStr = m.fecha || 'Sin fecha';

        html += `
            <tr>
                <td class="text-muted small">${fStr}</td>
                <td><i class="fa-solid fa-user-astronaut text-primary me-2"></i> ${m.usuario_nombre}</td>
                <td>${actionBadge}</td>
                <td class="fw-medium">${m.equipo_nombre}</td>
                <td class="text-muted small text-truncate" style="max-width: 200px;" title="${m.detalle}">${m.detalle}</td>
            </tr>
        `;
    });
    tbody.innerHTML = html;
}

function renderCharts(data) {
    Chart.defaults.color = '#9e9e9e';
    Chart.defaults.font.family = 'Inter';
    
    // State Chart
    const ctxState = document.getElementById('stateChart');
    if (ctxState) {
        if(stateChartInstance) stateChartInstance.destroy();
        stateChartInstance = new Chart(ctxState, {
            type: 'doughnut',
            data: {
                labels: ['Bueno', 'Regular', 'Malo'],
                datasets: [{
                    data: [data.buenos.cantidad, data.regulares.cantidad, data.malos.cantidad],
                    backgroundColor: ['#2e7d32', '#f57f17', '#c62828'],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: { legend: { display: false } }
            }
        });
    }
    
    // Category Chart
    const ctxCat = document.getElementById('categoryChart');
    if (ctxCat && data.por_categoria) {
        if(categoryChartInstance) categoryChartInstance.destroy();
        
        const labels = data.por_categoria.map(c => c.categoria);
        const values = data.por_categoria.map(c => c.cantidad);
        
        categoryChartInstance = new Chart(ctxCat, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Equipos',
                    data: values,
                    backgroundColor: 'rgba(26, 35, 126, 0.7)',
                    borderColor: '#1a237e',
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { precision: 0 } },
                    y: { grid: { display: false } }
                }
            }
        });
    }
}

// ---------------------------------------------------------
// INVENTORY LOGIC
// ---------------------------------------------------------

let currentSearch = '';
let currentEstado = '';
let currentCategoria = '';

function toggleForm() {
    const formSection = document.getElementById('formSection');
    if (!formSection) return;
    
    const isShowing = formSection.classList.contains('show');
    if (isShowing) {
        cancelEdit(); // Reset form if closing
        const bsCollapse = new bootstrap.Collapse(formSection, { toggle: false });
        bsCollapse.hide();
        document.getElementById('toggleFormText').textContent = 'Nuevo Equipo';
    } else {
        const bsCollapse = new bootstrap.Collapse(formSection, { toggle: false });
        bsCollapse.show();
        document.getElementById('toggleFormText').textContent = 'Cerrar Formulario';
        setTimeout(() => document.getElementById('codigo').focus(), 300);
    }
}

function clearFilters() {
    document.getElementById('searchFilter').value = '';
    document.getElementById('estadoFilter').value = '';
    document.getElementById('categoriaFilter').value = '';
    loadEquipos(1);
}

function loadEquipos(page = 1) {
    const s = document.getElementById('searchFilter')?.value || '';
    const e = document.getElementById('estadoFilter')?.value || '';
    const c = document.getElementById('categoriaFilter')?.value || '';
    
    currentSearch = s; currentEstado = e; currentCategoria = c;
    
    const tbody = document.getElementById('equiposTableBody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-5"><div class="spinner-border text-primary me-2" role="status"></div>Cargando datos...</td></tr>';
    
    fetch(`/api/equipos?search=${encodeURIComponent(s)}&estado=${encodeURIComponent(e)}&categoria=${encodeURIComponent(c)}&page=${page}&per_page=10`)
        .then(r => r.json())
        .then(data => {
            renderEquiposTable(data.equipos);
            renderPagination(data.total, data.pages, data.current_page);
            
            document.getElementById('tableInfo').textContent = 
                `Mostrando ${data.equipos.length} equipos de ${data.total} registrados.`;
        })
        .catch(err => {
            console.error('Error loading equipos:', err);
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-danger py-4">Error al cargar el inventario.</td></tr>';
        });
}

function renderEquiposTable(equipos) {
    const tbody = document.getElementById('equiposTableBody');
    if (equipos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-5">No se encontraron equipos que coincidan con los filtros.</td></tr>';
        return;
    }
    
    let html = '';
    equipos.forEach(e => {
        let badgeClass = e.estado === 'Bueno' ? 'success' : (e.estado === 'Regular' ? 'warning' : 'danger');
        let qtyClass = e.cantidad < 3 ? 'text-warning fw-bold' : '';
        
        let actionsHtml = `
            <button class="btn btn-sm btn-icon btn-outline-info border-0" onclick="viewEquipo(${e.id})" title="Ver Detalles">
                <i class="fa-solid fa-eye"></i>
            </button>
        `;
        
        // Solo Logistica o Admin pueden editar/eliminar
        if (CURRENT_USER.rol !== 'Consulta') {
            actionsHtml += `
                <button class="btn btn-sm btn-icon btn-outline-warning border-0" onclick="editEquipo(${e.id})" title="Editar Equipo">
                    <i class="fa-solid fa-pencil"></i>
                </button>
                <button class="btn btn-sm btn-icon btn-outline-danger border-0" onclick="confirmDelete(${e.id}, '${e.codigo}', '${e.nombre}')" title="Eliminar Equipo">
                    <i class="fa-solid fa-trash"></i>
                </button>
            `;
        }
        
        html += `
            <tr>
                <td><span class="font-monospace text-muted">${e.codigo}</span></td>
                <td class="fw-medium">${e.nombre}</td>
                <td class="text-center ${qtyClass}">${e.cantidad}</td>
                <td class="text-center"><span class="badge bg-${badgeClass} bg-opacity-25 text-${badgeClass}">${e.estado}</span></td>
                <td>${e.categoria}</td>
                <td class="text-muted small"><i class="fa-regular fa-clock me-1"></i>${e.fecha_registro || 'Sin fecha'}</td>
                <td class="text-center">
                    <div class="d-flex justify-content-center gap-1">
                        ${actionsHtml}
                    </div>
                </td>
            </tr>
        `;
    });
    tbody.innerHTML = html;
}

function renderPagination(total, pages, currentPage) {
    const ul = document.getElementById('paginationControls');
    if (!ul || pages <= 1) {
        if(ul) ul.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Prev
    html += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link glass-input border-0 bg-transparent text-light" href="#" onclick="event.preventDefault(); loadEquipos(${currentPage - 1})"><i class="fa-solid fa-chevron-left"></i></a>
             </li>`;
             
    // Numbers
    for (let i = 1; i <= pages; i++) {
        if (i === 1 || i === pages || (i >= currentPage - 1 && i <= currentPage + 1)) {
            let active = i === currentPage ? 'active' : '';
            html += `<li class="page-item ${active}">
                        <a class="page-link glass-input border-0 ${active ? 'bg-primary text-white fw-bold' : 'bg-transparent text-light'}" href="#" onclick="event.preventDefault(); loadEquipos(${i})">${i}</a>
                     </li>`;
        } else if (i === currentPage - 2 || i === currentPage + 2) {
            html += `<li class="page-item disabled"><span class="page-link glass-input border-0 bg-transparent text-muted">...</span></li>`;
        }
    }
    
    // Next
    html += `<li class="page-item ${currentPage === pages ? 'disabled' : ''}">
                <a class="page-link glass-input border-0 bg-transparent text-light" href="#" onclick="event.preventDefault(); loadEquipos(${currentPage + 1})"><i class="fa-solid fa-chevron-right"></i></a>
             </li>`;
             
    ul.innerHTML = html;
}

// Form Submit (Create/Update)
if (document.getElementById('equipoForm')) {
    document.getElementById('equipoForm').addEventListener('submit', function(e) {
        e.preventDefault();
        if (!this.checkValidity()) {
            this.classList.add('was-validated');
            return;
        }
        
        const id = document.getElementById('equipoId').value;
        const isUpdate = id !== '';
        
        const data = {
            codigo: document.getElementById('codigo').value,
            nombre: document.getElementById('nombre').value,
            cantidad: parseInt(document.getElementById('cantidad').value),
            estado: document.getElementById('estado').value,
            categoria: document.getElementById('categoria').value
        };
        
        const url = isUpdate ? `/api/equipos/${id}` : '/api/equipos';
        const method = isUpdate ? 'PUT' : 'POST';
        
        const btn = document.getElementById('btnSaveForm');
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Guardando...';
        btn.disabled = true;
        
        fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(r => r.json().then(d => ({status: r.status, body: d})))
        .then(res => {
            if (res.body.success) {
                showToast(res.body.message, 'success');
                cancelEdit(); // resets form
                loadEquipos(1); // reload table
                
                // Keep form open if we just added, close if we updated
                if (isUpdate) {
                    toggleForm();
                }
            } else {
                showToast(res.body.message, 'error');
            }
        })
        .catch(err => {
            console.error('Error:', err);
            showToast('Error de conexión con el servidor', 'error');
        })
        .finally(() => {
            btn.innerHTML = originalHtml;
            btn.disabled = false;
        });
    });
}

function editEquipo(id) {
    fetch(`/api/equipos/${id}`)
        .then(r => r.json())
        .then(data => {
            const equipo = data.equipo;
            // Fill form
            document.getElementById('equipoId').value = equipo.id;
            document.getElementById('codigo').value = equipo.codigo;
            document.getElementById('codigo').readOnly = true; // No se puede editar codigo
            document.getElementById('nombre').value = equipo.nombre;
            document.getElementById('cantidad').value = equipo.cantidad;
            document.getElementById('estado').value = equipo.estado;
            document.getElementById('categoria').value = equipo.categoria;
            
            // UI changes
            document.getElementById('formTitle').innerHTML = '<i class="fa-solid fa-pen-to-square me-2"></i> Editar Equipo';
            document.getElementById('btnSaveForm').innerHTML = '<i class="fa-solid fa-save me-2"></i> Actualizar Equipo';
            document.getElementById('btnCancelEdit').style.display = 'inline-block';
            document.getElementById('btnCancelForm').style.display = 'none';
            
            // Show form
            const formSection = document.getElementById('formSection');
            if (!formSection.classList.contains('show')) {
                toggleForm();
            } else {
                // Scroll to top slowly
                window.scrollTo({top: 0, behavior: 'smooth'});
            }
        })
        .catch(err => showToast('Error al cargar datos del equipo', 'error'));
}

function cancelEdit() {
    const form = document.getElementById('equipoForm');
    if (!form) return;
    form.reset();
    form.classList.remove('was-validated');
    
    document.getElementById('equipoId').value = '';
    document.getElementById('codigo').readOnly = false;
    
    document.getElementById('formTitle').innerHTML = '<i class="fa-solid fa-file-circle-plus me-2"></i> Registrar Nuevo Equipo';
    document.getElementById('btnSaveForm').innerHTML = '<i class="fa-solid fa-save me-2"></i> Guardar Equipo';
    document.getElementById('btnCancelEdit').style.display = 'none';
    document.getElementById('btnCancelForm').style.display = 'inline-block';
}

function viewEquipo(id) {
    fetch(`/api/equipos/${id}`)
        .then(r => r.json())
        .then(data => {
            const equipo = data.equipo;
            document.getElementById('viewCodigo').textContent = equipo.codigo;
            document.getElementById('viewNombre').textContent = equipo.nombre;
            document.getElementById('viewCantidad').textContent = equipo.cantidad;
            
            let badgeClass = equipo.estado === 'Bueno' ? 'success' : (equipo.estado === 'Regular' ? 'warning' : 'danger');
            document.getElementById('viewEstado').innerHTML = `<span class="badge bg-${badgeClass} fs-6">${equipo.estado}</span>`;
            
            document.getElementById('viewCategoria').textContent = equipo.categoria;
            
            // Usar fechas ya formateadas del backend (dd/mm/YYYY HH:MM)
            document.getElementById('viewRegistro').textContent = equipo.fecha_registro || 'Sin fecha';
            document.getElementById('viewModificacion').textContent = equipo.fecha_modificacion || 'Sin fecha';
            
            const modal = new bootstrap.Modal(document.getElementById('viewModal'));
            modal.show();
        })
        .catch(err => showToast('Error al cargar datos del equipo', 'error'));
}

function confirmDelete(id, codigo, nombre) {
    document.getElementById('deleteEquipoId').value = id;
    document.getElementById('deleteEquipoCodigo').textContent = codigo;
    document.getElementById('deleteEquipoNombre').textContent = nombre;
    
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
}

function executeDelete() {
    const id = document.getElementById('deleteEquipoId').value;
    
    fetch(`/api/equipos/${id}`, {
        method: 'DELETE'
    })
    .then(r => r.json())
    .then(data => {
        if(data.success) {
            bootstrap.Modal.getInstance(document.getElementById('deleteModal')).hide();
            showToast(data.message, 'success');
            loadEquipos(1);
        } else {
            showToast(data.message, 'error');
        }
    })
    .catch(err => showToast('Error de conexión', 'error'));
}

// ---------------------------------------------------------
// REPORTES LOGIC
// ---------------------------------------------------------

function toggleSubOptions() {
    const tipo = document.querySelector('input[name="tipoReporte"]:checked').value;
    
    document.getElementById('subOptionsContainer').classList.remove('show');
    document.getElementById('estadoSubOptions').classList.add('d-none');
    document.getElementById('categoriaSubOptions').classList.add('d-none');
    document.getElementById('movimientoSubOptions').classList.add('d-none');
    
    if (tipo === 'estado') {
        document.getElementById('estadoSubOptions').classList.remove('d-none');
        new bootstrap.Collapse(document.getElementById('subOptionsContainer'), {toggle: false}).show();
    } else if (tipo === 'categoria') {
        document.getElementById('categoriaSubOptions').classList.remove('d-none');
        new bootstrap.Collapse(document.getElementById('subOptionsContainer'), {toggle: false}).show();
    } else if (tipo === 'movimientos') {
        document.getElementById('movimientoSubOptions').classList.remove('d-none');
        new bootstrap.Collapse(document.getElementById('subOptionsContainer'), {toggle: false}).show();
    }
}

function generateReport() {
    const tipo = document.querySelector('input[name="tipoReporte"]:checked').value;
    let filtro = '';
    
    if (tipo === 'estado') filtro = document.getElementById('filtroEstado').value;
    if (tipo === 'categoria') filtro = document.getElementById('filtroCategoria').value;
    if (tipo === 'movimientos') filtro = document.getElementById('filtroMovimiento').value;
    
    const btn = document.getElementById('btnGenerarReporte');
    const ogHtml = btn.innerHTML;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Generando...';
    btn.disabled = true;
    
    fetch('/api/reportes/generar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tipo: tipo, filtro: filtro })
    })
    .then(r => r.json())
    .then(data => {
        // Hide selector, show report
        document.getElementById('reportSelectorSection').classList.add('d-none');
        
        const dispArea = document.getElementById('reportDisplayArea');
        dispArea.classList.remove('collapse');
        dispArea.classList.add('show');
        
        // Populate header
        document.getElementById('reportTitle').textContent = data.titulo;
        document.getElementById('reportDate').textContent = data.fecha_generacion;
        document.getElementById('reportUser').textContent = data.usuario;
        document.getElementById('reportFilters').textContent = data.filtros_aplicados;
        document.getElementById('reportTotalCount').textContent = data.total_registros;
        
        // Render Summary if available (not for movimientos usually)
        renderReportSummary(data.resumen, tipo);
        
        // Render Table
        renderReportTable(data.datos, tipo);
    })
    .catch(err => {
        console.error('Error generating report:', err);
        showToast('Error al generar el reporte', 'error');
    })
    .finally(() => {
        btn.innerHTML = ogHtml;
        btn.disabled = false;
    });
}

function renderReportSummary(resumen, tipo) {
    const container = document.getElementById('reportSummarySection');
    if (!resumen || Object.keys(resumen).length === 0 || tipo === 'movimientos') {
        container.innerHTML = '';
        return;
    }
    
    let html = `
        <div class="row text-center mb-4 g-2">
            <div class="col-sm-3">
                <div class="border rounded bg-light p-2">
                    <div class="small text-muted text-uppercase fw-bold">Total Equipos</div>
                    <div class="fs-4 fw-bold text-dark">${resumen.total}</div>
                </div>
            </div>
            <div class="col-sm-3">
                <div class="border rounded bg-success bg-opacity-10 p-2">
                    <div class="small text-success text-uppercase fw-bold">Buen Estado</div>
                    <div class="fs-4 fw-bold text-success">${resumen.buenos || 0}</div>
                </div>
            </div>
            <div class="col-sm-3">
                <div class="border rounded bg-warning bg-opacity-10 p-2">
                    <div class="small text-warning text-uppercase fw-bold text-dark">Regulares</div>
                    <div class="fs-4 fw-bold text-dark">${resumen.regulares || 0}</div>
                </div>
            </div>
            <div class="col-sm-3">
                <div class="border rounded bg-danger bg-opacity-10 p-2">
                    <div class="small text-danger text-uppercase fw-bold">Mal Estado</div>
                    <div class="fs-4 fw-bold text-danger">${resumen.malos || 0}</div>
                </div>
            </div>
        </div>
    `;
    container.innerHTML = html;
}

function renderReportTable(datos, tipo) {
    const thead = document.getElementById('reportTableHeader');
    const tbody = document.getElementById('reportTableBody');
    
    if (datos.length === 0) {
        thead.innerHTML = '<tr><th>Datos</th></tr>';
        tbody.innerHTML = '<tr><td class="text-center py-4">No se encontraron registros para los filtros seleccionados.</td></tr>';
        return;
    }
    
    if (tipo === 'movimientos') {
        thead.innerHTML = `
            <tr>
                <th>Fecha/Hora</th>
                <th>Usuario</th>
                <th>Acción</th>
                <th>Equipo</th>
                <th>Detalle</th>
            </tr>
        `;
        let html = '';
        datos.forEach(d => {
            html += `
                <tr>
                    <td>${d.fecha}</td>
                    <td>${d.usuario_nombre}</td>
                    <td>${d.accion}</td>
                    <td>${d.equipo_codigo} - ${d.equipo_nombre}</td>
                    <td><small>${d.detalle || ''}</small></td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    } else {
        // Equipos
        thead.innerHTML = `
            <tr>
                <th>Código</th>
                <th>Nombre</th>
                <th class="text-center">Cantidad</th>
                <th class="text-center">Estado</th>
                <th>Categoría</th>
            </tr>
        `;
        let html = '';
        datos.forEach(d => {
            html += `
                <tr>
                    <td><strong>${d.codigo}</strong></td>
                    <td>${d.nombre}</td>
                    <td class="text-center">${d.cantidad}</td>
                    <td class="text-center">${d.estado}</td>
                    <td>${d.categoria}</td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    }
}

function newReport() {
    document.getElementById('reportDisplayArea').classList.remove('show');
    document.getElementById('reportDisplayArea').classList.add('collapse');
    document.getElementById('reportSelectorSection').classList.remove('d-none');
}

function printReport() {
    window.print();
}

function exportReport(format) {
    const tipo = document.querySelector('input[name="tipoReporte"]:checked').value;
    let filtro = '';
    if (tipo === 'estado') filtro = document.getElementById('filtroEstado').value;
    if (tipo === 'categoria') filtro = document.getElementById('filtroCategoria').value;
    if (tipo === 'movimientos') filtro = document.getElementById('filtroMovimiento').value;
    
    const url = `/api/reportes/exportar/${format}?tipo=${tipo}&filtro=${encodeURIComponent(filtro)}`;
    window.open(url, '_blank');
}

// ---------------------------------------------------------
// USUARIOS LOGIC (Admin only)
// ---------------------------------------------------------

function toggleUserForm() {
    const formSection = document.getElementById('userFormSection');
    if (!formSection) return;
    
    const isShowing = formSection.classList.contains('show');
    if (isShowing) {
        cancelUserEdit();
        new bootstrap.Collapse(formSection, { toggle: false }).hide();
        document.getElementById('toggleUserFormText').textContent = 'Nuevo Usuario';
    } else {
        new bootstrap.Collapse(formSection, { toggle: false }).show();
        document.getElementById('toggleUserFormText').textContent = 'Cerrar Formulario';
        document.getElementById('nombre_completo').focus();
    }
}

function loadUsuarios() {
    const tbody = document.getElementById('usuariosTableBody');
    if (!tbody) return;
    
    fetch('/api/usuarios')
        .then(r => r.json())
        .then(data => {
            const usuarios = data.usuarios || [];
            if(usuarios.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4">No hay usuarios registrados.</td></tr>';
                return;
            }
            
            let html = '';
            usuarios.forEach(u => {
                let badgeClass = u.rol === 'Administrador' ? 'primary' : (u.rol === 'Logística' ? 'success' : 'info');
                let isMe = u.nombre_usuario === CURRENT_USER.nombre_usuario;
                
                let toggleBtn = isMe ? '' : `
                    <button class="btn btn-sm btn-icon ${u.estado === 'Activo' ? 'btn-outline-warning' : 'btn-outline-success'} border-0" 
                            onclick="toggleUserStatus(${u.id})" title="${u.estado === 'Activo' ? 'Desactivar' : 'Activar'}">
                        <i class="fa-solid ${u.estado === 'Activo' ? 'fa-ban' : 'fa-check'}"></i>
                    </button>
                `;
                
                let resetBtn = isMe ? '' : `
                    <button class="btn btn-sm btn-icon btn-outline-danger border-0" 
                            onclick="resetPassword(${u.id})" title="Restablecer Contraseña">
                        <i class="fa-solid fa-key"></i>
                    </button>
                `;
                
                html += `
                    <tr class="${u.estado !== 'Activo' ? 'opacity-50' : ''}">
                        <td class="fw-medium">${u.nombre_completo} ${isMe ? '<span class="badge bg-secondary ms-1">Tú</span>' : ''}</td>
                        <td class="text-muted small">${u.grado_cargo}</td>
                        <td><span class="font-monospace">${u.nombre_usuario}</span></td>
                        <td class="text-center"><span class="badge bg-${badgeClass} bg-opacity-25 text-${badgeClass}">${u.rol}</span></td>
                        <td class="text-center">
                            <span class="badge ${u.estado === 'Activo' ? 'bg-success text-white' : 'bg-danger text-white'}">${u.estado}</span>
                        </td>
                        <td class="text-center">
                            <div class="d-flex justify-content-center gap-1">
                                <button class="btn btn-sm btn-icon btn-outline-info border-0" onclick="editUsuario(${u.id})" title="Editar Perfil">
                                    <i class="fa-solid fa-pencil"></i>
                                </button>
                                ${toggleBtn}
                                ${resetBtn}
                            </div>
                        </td>
                    </tr>
                `;
            });
            tbody.innerHTML = html;
        })
        .catch(err => {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger py-4">Error cargando usuarios.</td></tr>';
        });
}

function saveUsuario() {
    const form = document.getElementById('usuarioForm');
    if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return;
    }
    
    const pass = document.getElementById('password').value;
    const conf = document.getElementById('confirmar_password').value;
    const id = document.getElementById('usuarioId').value;
    const isUpdate = id !== '';
    
    // Check passwords match on create, or if typing new pass on update
    if (!isUpdate || (isUpdate && pass)) {
        if (pass !== conf) {
            document.getElementById('confirmar_password').setCustomValidity("Las contraseñas no coinciden");
            form.classList.add('was-validated');
            return;
        } else {
            document.getElementById('confirmar_password').setCustomValidity("");
        }
    }
    
    const data = {
        nombre_completo: document.getElementById('nombre_completo').value,
        grado_cargo: document.getElementById('grado_cargo').value,
        nombre_usuario: document.getElementById('nombre_usuario').value,
        rol: document.getElementById('rol').value
    };
    
    if (pass) data.password = pass; // Only send password if typed
    
    const url = isUpdate ? `/api/usuarios/${id}` : '/api/usuarios';
    const method = isUpdate ? 'PUT' : 'POST';
    
    const btn = document.getElementById('btnSaveUser');
    const ogHtml = btn.innerHTML;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Guardando...';
    btn.disabled = true;
    
    fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            cancelUserEdit();
            loadUsuarios();
            if(!isUpdate) toggleUserForm();
        } else {
            showToast(data.message, 'error');
        }
    })
    .catch(err => showToast('Error de servidor', 'error'))
    .finally(() => {
        btn.innerHTML = ogHtml;
        btn.disabled = false;
    });
}

function editUsuario(id) {
    // Fetch all users and find this one (since we don't have a single user GET API defined in requirements, we use the list)
    fetch('/api/usuarios')
        .then(r => r.json())
        .then(data => {
            const u = (data.usuarios || []).find(x => x.id === id);
            if (!u) return;
            
            document.getElementById('usuarioId').value = u.id;
            document.getElementById('nombre_completo').value = u.nombre_completo;
            document.getElementById('grado_cargo').value = u.grado_cargo;
            document.getElementById('nombre_usuario').value = u.nombre_usuario;
            document.getElementById('nombre_usuario').readOnly = true;
            document.getElementById('rol').value = u.rol;
            
            // Passwords not required on edit
            document.getElementById('password').required = false;
            document.getElementById('confirmar_password').required = false;
            
            // UI
            document.getElementById('userFormTitle').innerHTML = '<i class="fa-solid fa-user-pen me-2"></i> Editar Usuario';
            document.getElementById('btnSaveUser').innerHTML = '<i class="fa-solid fa-save me-2"></i> Actualizar Usuario';
            document.getElementById('btnCancelUserEdit').style.display = 'inline-block';
            document.getElementById('btnCancelUserForm').style.display = 'none';
            
            const formSection = document.getElementById('userFormSection');
            if (!formSection.classList.contains('show')) toggleUserForm();
        });
}

function cancelUserEdit() {
    const form = document.getElementById('usuarioForm');
    if (!form) return;
    form.reset();
    form.classList.remove('was-validated');
    
    document.getElementById('usuarioId').value = '';
    document.getElementById('nombre_usuario').readOnly = false;
    document.getElementById('password').required = true;
    document.getElementById('confirmar_password').required = true;
    
    document.getElementById('userFormTitle').innerHTML = '<i class="fa-solid fa-user-gear me-2"></i> Registrar Nuevo Usuario';
    document.getElementById('btnSaveUser').innerHTML = '<i class="fa-solid fa-save me-2"></i> Guardar Usuario';
    document.getElementById('btnCancelUserEdit').style.display = 'none';
    document.getElementById('btnCancelUserForm').style.display = 'inline-block';
}

function toggleUserStatus(id) {
    if(!confirm("¿Cambiar el estado de acceso de este usuario?")) return;
    
    fetch(`/api/usuarios/${id}/toggle`, { method: 'PATCH' })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showToast(data.message, 'success');
                loadUsuarios();
            } else {
                showToast(data.message, 'error');
            }
        });
}

function resetPassword(id) {
    if(!confirm("¿Restablecer la contraseña a 'sar12345'? El usuario deberá cambiarla luego.")) return;
    
    fetch(`/api/usuarios/${id}/reset-password`, { method: 'PATCH' })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showToast(data.message, 'success');
            } else {
                showToast(data.message, 'error');
            }
        });
}
