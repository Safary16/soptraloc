/**
 * Reloj en Tiempo Real estilo Torre de Control Aéreo
 * Sistema de monitoreo con alertas de contenedores urgentes
 */

class ATCClock {
    constructor() {
        this.timeElement = null;
        this.dateElement = null;
        this.urgentBadge = null;
        this.urgentCount = 0;
        this.urgentContainers = [];
        this.REFRESH_INTERVAL = 1000; // 1 segundo
        this.URGENT_CHECK_INTERVAL = 30000; // 30 segundos
    }

    init() {
        console.log('🕐 Iniciando reloj ATC...');
        
        // Esperar a que el DOM esté listo
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }

    setup() {
        this.timeElement = document.getElementById('atc-clock-time');
        this.dateElement = document.getElementById('atc-clock-date');
        this.urgentBadge = document.getElementById('atc-urgent-badge');

        if (!this.timeElement || !this.dateElement) {
            console.error('❌ Elementos del reloj no encontrados');
            return;
        }
        
        // Iniciar reloj
        this.updateClock();
        setInterval(() => this.updateClock(), this.REFRESH_INTERVAL);
        
        // Verificar contenedores urgentes
        this.checkUrgentContainers();
        setInterval(() => this.checkUrgentContainers(), this.URGENT_CHECK_INTERVAL);
        
        // Configurar modal de urgentes
        this.setupUrgentModal();
        
        console.log('✅ Reloj ATC iniciado correctamente');
    }

    updateClock() {
        const now = new Date();
        
        // Formato de tiempo: HH:MM:SS
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        this.timeElement.textContent = `${hours}:${minutes}:${seconds}`;
        
        // Formato de fecha: DÍA DD MES YYYY
        const days = ['DOM', 'LUN', 'MAR', 'MIÉ', 'JUE', 'VIE', 'SÁB'];
        const months = ['ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC'];
        
        const dayName = days[now.getDay()];
        const day = String(now.getDate()).padStart(2, '0');
        const month = months[now.getMonth()];
        const year = now.getFullYear();
        
        this.dateElement.textContent = `${dayName} ${day} ${month} ${year}`;
    }

    async checkUrgentContainers() {
        try {
            // Verificar si estamos en la página del dashboard
            if (!window.location.pathname.includes('/dashboard/')) {
                return;
            }

            const response = await fetch('/api/v1/containers/urgent/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.urgentContainers = data.containers || [];
                this.urgentCount = this.urgentContainers.length;
                this.updateUrgentBadge();
            }
        } catch (error) {
            console.warn('⚠️ No se pudo verificar contenedores urgentes:', error);
        }
    }

    updateUrgentBadge() {
        if (this.urgentBadge) {
            if (this.urgentCount > 0) {
                this.urgentBadge.textContent = this.urgentCount;
                this.urgentBadge.style.display = 'flex';
                this.urgentBadge.title = `${this.urgentCount} contenedor${this.urgentCount > 1 ? 'es' : ''} urgente${this.urgentCount > 1 ? 's' : ''}`;
            } else {
                this.urgentBadge.style.display = 'none';
            }
        }
    }

    setupUrgentModal() {
        // Verificar si el modal ya existe
        if (document.getElementById('urgentModal')) {
            return;
        }

        // Crear modal para contenedores urgentes
        const modalHTML = `
            <div class="modal fade" id="urgentModal" tabindex="-1" aria-labelledby="urgentModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg modal-dialog-scrollable">
                    <div class="modal-content">
                        <div class="modal-header bg-danger text-white">
                            <h5 class="modal-title" id="urgentModalLabel">
                                <i class="bi bi-exclamation-triangle-fill"></i>
                                Contenedores Urgentes
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div id="urgent-containers-list">
                                <div class="text-center text-muted py-4">
                                    <div class="spinner-border" role="status">
                                        <span class="visually-hidden">Cargando...</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                            <a href="/dashboard/" class="btn btn-primary">
                                <i class="bi bi-speedometer2"></i> Ir al Dashboard
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Event listener para cargar contenedores cuando se abre el modal
        const modal = document.getElementById('urgentModal');
        if (modal) {
            modal.addEventListener('show.bs.modal', () => this.loadUrgentContainersModal());
        }
    }

    loadUrgentContainersModal() {
        const listContainer = document.getElementById('urgent-containers-list');
        if (!listContainer) return;

        if (this.urgentContainers.length === 0) {
            listContainer.innerHTML = `
                <div class="alert alert-success" role="alert">
                    <i class="bi bi-check-circle-fill"></i>
                    <strong>¡Todo en orden!</strong><br>
                    No hay contenedores urgentes en este momento.
                </div>
            `;
            return;
        }

        let html = '<div class="list-group">';
        
        this.urgentContainers.forEach(container => {
            const urgencyClass = this.getUrgencyClass(container.urgency_level);
            const urgencyIcon = this.getUrgencyIcon(container.urgency_level);
            
            html += `
                <div class="list-group-item ${urgencyClass}">
                    <div class="d-flex w-100 justify-content-between align-items-start">
                        <div>
                            <h6 class="mb-1">
                                <i class="${urgencyIcon}"></i>
                                <strong>${container.container_number}</strong>
                            </h6>
                            <p class="mb-1">
                                <strong>Cliente:</strong> ${container.client || 'N/A'}<br>
                                <strong>Ubicación:</strong> ${container.location || 'N/A'}<br>
                                <strong>Fecha programada:</strong> ${container.scheduled_date || 'N/A'}<br>
                                <strong>Estado:</strong> <span class="badge bg-secondary">${container.status || 'N/A'}</span>
                            </p>
                        </div>
                        <div class="text-end">
                            <span class="badge bg-danger fs-6">
                                ${container.hours_remaining ? `${container.hours_remaining.toFixed(1)}h restantes` : 'URGENTE'}
                            </span>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        listContainer.innerHTML = html;
    }

    getUrgencyClass(level) {
        const classes = {
            'critical': 'list-group-item-danger',
            'high': 'list-group-item-warning',
            'medium': 'list-group-item-info'
        };
        return classes[level] || '';
    }

    getUrgencyIcon(level) {
        const icons = {
            'critical': 'bi bi-exclamation-triangle-fill text-danger',
            'high': 'bi bi-exclamation-circle-fill text-warning',
            'medium': 'bi bi-clock-fill text-info'
        };
        return icons[level] || 'bi bi-clock';
    }

    getUrgentContainers() {
        return this.urgentContainers;
    }
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        window.atcClock = new ATCClock();
        window.atcClock.init();
    });
} else {
    // DOM ya está listo
    window.atcClock = new ATCClock();
    window.atcClock.init();
}
