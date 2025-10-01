/**
 * Reloj en tiempo real y sistema de alertas de proximidad
 * Muestra fecha/hora actual y notificaciones de contenedores urgentes
 */

(function() {
    'use strict';

    const REFRESH_INTERVAL = 1000; // Actualizar cada segundo
    const ALERT_CHECK_INTERVAL = 60000; // Revisar alertas cada minuto
    const ALERT_THRESHOLD_HOURS = 2; // Alertar si falta menos de 2 horas

    class RealtimeClock {
        constructor() {
            this.clockElement = null;
            this.alertBadge = null;
            this.urgentContainers = [];
            this.init();
        }

        init() {
            // Esperar a que el DOM esté listo
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.setup());
            } else {
                this.setup();
            }
        }

        setup() {
            this.injectClockHTML();
            this.clockElement = document.getElementById('realtime-clock');
            this.alertBadge = document.getElementById('urgent-alert-badge');
            
            if (this.clockElement) {
                this.startClock();
                this.checkUrgentContainers();
                setInterval(() => this.checkUrgentContainers(), ALERT_CHECK_INTERVAL);
            }
        }

        injectClockHTML() {
            const navbar = document.querySelector('.navbar .container');
            if (!navbar) return;

            // Buscar o crear el contenedor del reloj
            let clockContainer = navbar.querySelector('.clock-container');
            if (!clockContainer) {
                clockContainer = document.createElement('div');
                clockContainer.className = 'clock-container d-flex align-items-center';
                clockContainer.style.marginLeft = 'auto';
                clockContainer.style.marginRight = '1rem';
                
                clockContainer.innerHTML = `
                    <div class="text-white me-3" id="realtime-clock">
                        <i class="bi bi-clock"></i>
                        <span id="clock-time">--:--:--</span>
                        <br>
                        <small id="clock-date" style="font-size: 0.75rem;">-- -- ----</small>
                    </div>
                    <div class="position-relative" id="urgent-alerts-container" style="display: none;">
                        <button class="btn btn-sm btn-outline-light position-relative" 
                                id="urgent-alerts-btn"
                                data-bs-toggle="modal" 
                                data-bs-target="#urgentAlertsModal">
                            <i class="bi bi-exclamation-triangle-fill"></i>
                            <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger" 
                                  id="urgent-alert-badge">0</span>
                        </button>
                    </div>
                `;
                
                // Insertar antes del navbar-nav
                const navbarNav = navbar.querySelector('.navbar-nav');
                if (navbarNav) {
                    navbar.insertBefore(clockContainer, navbarNav);
                } else {
                    navbar.appendChild(clockContainer);
                }
            }

            // Inyectar modal de alertas urgentes
            this.injectAlertsModal();
        }

        injectAlertsModal() {
            if (document.getElementById('urgentAlertsModal')) return;

            const modalHTML = `
                <div class="modal fade" id="urgentAlertsModal" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header bg-danger text-white">
                                <h5 class="modal-title">
                                    <i class="bi bi-exclamation-triangle-fill"></i>
                                    Contenedores Urgentes (< 2 horas)
                                </h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div id="urgent-containers-list">
                                    <div class="text-center text-muted">
                                        <div class="spinner-border" role="status">
                                            <span class="visually-hidden">Cargando...</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                                <a href="/dashboard/" class="btn btn-primary">Ir al Dashboard</a>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', modalHTML);

            // Event listener para cargar contenedores al abrir modal
            const modal = document.getElementById('urgentAlertsModal');
            modal.addEventListener('show.bs.modal', () => this.loadUrgentContainersModal());
        }

        startClock() {
            this.updateClock();
            setInterval(() => this.updateClock(), REFRESH_INTERVAL);
        }

        updateClock() {
            const now = new Date();
            
            // Formatear hora: HH:MM:SS
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const seconds = String(now.getSeconds()).padStart(2, '0');
            const timeString = `${hours}:${minutes}:${seconds}`;
            
            // Formatear fecha: DD MMM YYYY
            const days = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
            const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
            const dayName = days[now.getDay()];
            const day = String(now.getDate()).padStart(2, '0');
            const month = months[now.getMonth()];
            const year = now.getFullYear();
            const dateString = `${dayName} ${day} ${month} ${year}`;
            
            // Actualizar DOM
            const timeElement = document.getElementById('clock-time');
            const dateElement = document.getElementById('clock-date');
            
            if (timeElement) timeElement.textContent = timeString;
            if (dateElement) dateElement.textContent = dateString;
        }

        async checkUrgentContainers() {
            try {
                const response = await fetch('/api/containers/urgent/');
                if (!response.ok) return;
                
                const data = await response.json();
                this.urgentContainers = data.urgent_containers || [];
                
                // Actualizar badge
                const count = this.urgentContainers.length;
                if (this.alertBadge) {
                    this.alertBadge.textContent = count;
                }
                
                // Mostrar/ocultar botón de alertas
                const alertsContainer = document.getElementById('urgent-alerts-container');
                if (alertsContainer) {
                    alertsContainer.style.display = count > 0 ? 'block' : 'none';
                }
                
                // Notificación sonora/visual si hay nuevos urgentes críticos
                this.notifyIfCritical();
                
            } catch (error) {
                console.error('Error checking urgent containers:', error);
            }
        }

        notifyIfCritical() {
            const criticalCount = this.urgentContainers.filter(c => c.urgency_level === 'critical').length;
            
            if (criticalCount > 0 && this.alertBadge) {
                // Animación de pulso en el badge
                this.alertBadge.classList.add('animate-pulse');
                setTimeout(() => this.alertBadge.classList.remove('animate-pulse'), 2000);
            }
        }

        loadUrgentContainersModal() {
            const listContainer = document.getElementById('urgent-containers-list');
            if (!listContainer) return;
            
            if (this.urgentContainers.length === 0) {
                listContainer.innerHTML = `
                    <div class="text-center text-muted py-4">
                        <i class="bi bi-check-circle" style="font-size: 3rem;"></i>
                        <p class="mt-2">No hay contenedores urgentes en este momento</p>
                    </div>
                `;
                return;
            }
            
            let html = '<div class="list-group">';
            
            this.urgentContainers.forEach(container => {
                const urgencyClass = this.getUrgencyClass(container.urgency_level);
                const urgencyIcon = this.getUrgencyIcon(container.urgency_level);
                const urgencyText = this.getUrgencyText(container.urgency_level);
                
                html += `
                    <div class="list-group-item ${urgencyClass}">
                        <div class="d-flex w-100 justify-content-between align-items-start">
                            <div>
                                <h6 class="mb-1">
                                    <i class="${urgencyIcon}"></i>
                                    ${container.container_number}
                                </h6>
                                <p class="mb-1">
                                    <strong>Cliente:</strong> ${container.client || 'N/A'}<br>
                                    <strong>CD:</strong> ${container.cd_location || 'N/A'}<br>
                                    <strong>Programado:</strong> ${container.scheduled_date} ${container.scheduled_time}
                                </p>
                            </div>
                            <div class="text-end">
                                <span class="badge bg-${urgencyClass === 'list-group-item-danger' ? 'danger' : urgencyClass === 'list-group-item-warning' ? 'warning' : 'info'}">
                                    ${urgencyText}
                                </span>
                                <div class="mt-2">
                                    <small class="text-muted">Faltan: ${this.formatTimeRemaining(container.hours_remaining)}</small>
                                </div>
                                ${container.status === 'PROGRAMADO' ? `
                                    <a href="/containers/${container.id}/" class="btn btn-sm btn-primary mt-2">
                                        Asignar Ahora
                                    </a>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            listContainer.innerHTML = html;
        }

        getUrgencyClass(level) {
            return {
                'critical': 'list-group-item-danger',
                'high': 'list-group-item-warning',
                'medium': 'list-group-item-info'
            }[level] || '';
        }

        getUrgencyIcon(level) {
            return {
                'critical': 'bi bi-exclamation-triangle-fill text-danger',
                'high': 'bi bi-exclamation-circle-fill text-warning',
                'medium': 'bi bi-clock-fill text-info'
            }[level] || 'bi bi-clock';
        }

        getUrgencyText(level) {
            return {
                'critical': '¡CRÍTICO!',
                'high': 'Alta Prioridad',
                'medium': 'Prioridad Media'
            }[level] || 'Normal';
        }

        formatTimeRemaining(hours) {
            const h = Math.floor(hours);
            const m = Math.floor((hours - h) * 60);
            
            if (h > 0) {
                return `${h}h ${m}min`;
            } else {
                return `${m} minutos`;
            }
        }
    }

    // Inicializar el reloj cuando se cargue el script
    const clock = new RealtimeClock();

    // Exportar para uso global si es necesario
    window.RealtimeClock = clock;

    // CSS para animación de pulso
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.2); }
        }
        .animate-pulse {
            animation: pulse 0.5s ease-in-out 3;
        }
        #realtime-clock {
            font-family: 'Courier New', monospace;
            text-align: right;
        }
        #clock-time {
            font-size: 1.1rem;
            font-weight: bold;
        }
    `;
    document.head.appendChild(style);

})();
