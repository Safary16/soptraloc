// Main JavaScript para SoptraLoc TMS

// Formatear números con separador de miles
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

// Actualizar reloj en tiempo real
function updateClock() {
    const now = new Date();
    const options = { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        timeZone: 'America/Santiago'
    };
    const clockElement = document.getElementById('realtime-clock');
    if (clockElement) {
        clockElement.textContent = now.toLocaleDateString('es-CL', options);
    }
}

// Actualizar cada segundo
if (document.getElementById('realtime-clock')) {
    setInterval(updateClock, 1000);
    updateClock();
}

// Cargar datos del dashboard vía API
async function loadDashboardData() {
    try {
        const response = await fetch('/api/programaciones/dashboard/');
        const data = await response.json();
        
        if (data.success) {
            await updateDashboardStats(data);
            updateProgramacionesTable(data.programaciones);
        }
    } catch (error) {
        console.error('Error cargando datos del dashboard:', error);
    }
}

// Actualizar estadísticas del dashboard
async function updateDashboardStats(data) {
    const criticas = data.programaciones.filter(p => p.urgencia === 'CRÍTICA').length;
    const altas = data.programaciones.filter(p => p.urgencia === 'ALTA').length;
    
    // Fetch containers count from API
    try {
        const containersResponse = await fetch('/api/containers/?format=json');
        const containersData = await containersResponse.json();
        const containersCount = containersData.count || containersData.length || 0;
        
        if (document.getElementById('stat-total')) {
            document.getElementById('stat-total').textContent = containersCount;
        }
    } catch (error) {
        console.error('Error fetching containers count:', error);
        // Fallback to programaciones count if containers fetch fails
        if (document.getElementById('stat-total')) {
            document.getElementById('stat-total').textContent = data.total || 0;
        }
    }
    
    if (document.getElementById('stat-criticas')) {
        document.getElementById('stat-criticas').textContent = criticas;
    }
    if (document.getElementById('stat-altas')) {
        document.getElementById('stat-altas').textContent = altas;
    }
}

// Actualizar tabla de programaciones
function updateProgramacionesTable(programaciones) {
    const tbody = document.getElementById('programaciones-tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    programaciones.slice(0, 10).forEach(prog => {
        const row = document.createElement('tr');
        
        // Badge de urgencia
        let badgeClass = 'badge-urgencia-baja';
        if (prog.urgencia === 'CRÍTICA') badgeClass = 'badge-urgencia-critica';
        else if (prog.urgencia === 'ALTA') badgeClass = 'badge-urgencia-alta';
        else if (prog.urgencia === 'MEDIA') badgeClass = 'badge-urgencia-media';
        
        row.innerHTML = `
            <td><strong>${prog.container_id}</strong></td>
            <td>${prog.cd}</td>
            <td>${prog.conductor || '<span class="text-muted">Sin asignar</span>'}</td>
            <td>${prog.dias_hasta_programacion.toFixed(1)}d</td>
            <td>${prog.dias_hasta_demurrage ? prog.dias_hasta_demurrage.toFixed(1) + 'd' : 'N/A'}</td>
            <td><span class="badge ${badgeClass}">${prog.urgencia}</span></td>
        `;
        
        tbody.appendChild(row);
    });
}

// Auto-refresh cada 30 segundos
if (document.getElementById('programaciones-tbody')) {
    loadDashboardData();
    setInterval(loadDashboardData, 30000);
}

// Tooltip de Bootstrap
const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

console.log('🚀 SoptraLoc TMS - Sistema cargado correctamente');
