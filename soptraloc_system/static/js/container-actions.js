(function (window, document) {
    'use strict';

    const POSITION_LABELS = {
        EN_PISO: 'En Piso',
        EN_CHASIS: 'En Chasis',
        EN_RUTA: 'En Ruta',
        CCTI: 'CCTI - Base Maipú',
        ZEAL: 'ZEAL',
        CLEP: 'CLEP',
        CD_QUILICURA: 'CD Quilicura',
        CD_CAMPOS: 'CD Campos',
        CD_MADERO: 'CD Puerto Madero',
        CD_PENON: 'CD El Peñón',
        DEPOSITO_DEVOLUCION: 'Depósito Devolución'
    };

    const ARRIVAL_OPTIONS = [
        { value: 'CCTI', label: 'CCTI (Retorna vacío a base)' },
        { value: 'DEPOSITO_DEVOLUCION', label: 'Depósito de Devolución (Devuelto vacío)' },
        { value: 'CD_QUILICURA', label: 'CD Quilicura' },
        { value: 'CD_PENON', label: 'CD El Peñón' },
        { value: 'CD_MADERO', label: 'CD Puerto Madero' },
        { value: 'CD_CAMPOS', label: 'CD Campos' },
        { value: 'EN_PISO', label: 'En Piso' },
        { value: 'EN_CHASIS', label: 'En Chasis' }
    ];

    const actions = {};

    function getCsrfToken() {
        if (typeof window.getCookie === 'function') {
            return window.getCookie('csrftoken');
        }
        const name = 'csrftoken';
        const cookies = document.cookie ? document.cookie.split(';') : [];
        for (let i = 0; i < cookies.length; i += 1) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                return decodeURIComponent(cookie.substring(name.length + 1));
            }
        }
        return null;
    }

    function ensureCsrfInput() {
        if (!document.querySelector('input[name="csrfmiddlewaretoken"]')) {
            const token = getCsrfToken();
            if (token) {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'csrfmiddlewaretoken';
                input.value = token;
                document.body.appendChild(input);
            }
        }
    }

    function fetchWithCsrf(url, options) {
        const opts = Object.assign({ credentials: 'same-origin' }, options || {});
        const headers = new Headers(opts.headers || {});
        if (!headers.has('X-CSRFToken')) {
            const csrfToken = getCsrfToken();
            if (csrfToken) {
                headers.set('X-CSRFToken', csrfToken);
            }
        }
        opts.headers = headers;
        return fetch(url, opts);
    }

    function handleJsonResponse(response) {
        if (!response.ok) {
            return response.json().catch(() => ({})).then((payload) => {
                const message = payload.detail || payload.message || `Error ${response.status}`;
                const error = new Error(message);
                error.payload = payload;
                throw error;
            });
        }
        return response.json();
    }

    function postJson(url, payload, options) {
        return fetchWithCsrf(url, Object.assign({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload || {})
        }, options)).then(handleJsonResponse);
    }

    function postForm(url, formData, options) {
        return fetchWithCsrf(url, Object.assign({
            method: 'POST',
            body: formData
        }, options)).then(handleJsonResponse);
    }

    function showAlert(type, message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 320px;';
        alertDiv.innerHTML = `
            <div class="d-flex align-items-center gap-2">
                <i class="bi ${type === 'success' ? 'bi-check-circle-fill' : type === 'warning' ? 'bi-exclamation-circle-fill' : 'bi-x-circle-fill'}"></i>
                <span>${message}</span>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        document.body.appendChild(alertDiv);
        setTimeout(() => {
            if (alertDiv && alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    function reloadAfterDelay(delayMs) {
        setTimeout(() => {
            window.location.reload();
        }, delayMs || 1500);
    }

    function confirmAction(message) {
        return !message || window.confirm(message);
    }

    function createArrivalModal(containerId) {
        const modalId = 'arrivalModal';
        const existing = document.getElementById(modalId);
        if (existing) {
            existing.remove();
        }

        const optionsHtml = ARRIVAL_OPTIONS.map(({ value, label }) => `<option value="${value}">${label}</option>`).join('');
        const modalHtml = `
            <div class="modal fade" id="${modalId}" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Marcar Arribo</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
                        </div>
                        <div class="modal-body">
                            <label class="form-label">Seleccionar destino de arribo:</label>
                            <select class="form-select" id="arrivalLocationSelect">
                                ${optionsHtml}
                            </select>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                            <button type="button" class="btn btn-success" data-action="confirm-arrival">Confirmar Arribo</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const element = document.getElementById(modalId);
        element.querySelector('[data-action="confirm-arrival"]').addEventListener('click', () => {
            const select = element.querySelector('select');
            const location = select ? select.value : null;
            if (!location) {
                showAlert('warning', 'Debe seleccionar un destino de arribo');
                return;
            }
            actions.markArrived(containerId, location);
            const instance = bootstrap.Modal.getInstance(element);
            if (instance) {
                instance.hide();
            }
        });

        return new bootstrap.Modal(element);
    }

    function updateStatus(containerId, payload, options) {
        const settings = Object.assign({
            confirmMessage: null,
            successMessage: null,
            reload: true,
            delay: 1500
        }, options || {});

        if (!confirmAction(settings.confirmMessage)) {
            return Promise.resolve(null);
        }

        return postJson(`/containers/${containerId}/update-status/`, payload).then((data) => {
            if (data.success) {
                showAlert('success', data.message || settings.successMessage || 'Estado actualizado correctamente');
                if (settings.reload) {
                    reloadAfterDelay(settings.delay);
                }
            } else {
                showAlert('danger', data.message || 'No fue posible actualizar el estado');
            }
            return data;
        }).catch((error) => {
            showAlert('danger', error.message || 'Error al actualizar estado');
            throw error;
        });
    }

    function renderDriverModal(container, drivers) {
        const modalId = 'driverModal';
        const existing = document.getElementById(modalId);
        if (existing) {
            existing.remove();
        }

        let bodyHtml = '<p class="text-muted">No hay conductores disponibles</p>';
        if (Array.isArray(drivers) && drivers.length > 0) {
            bodyHtml = '<div class="list-group">' + drivers.map((driver) => `
                <button type="button" class="list-group-item list-group-item-action" data-driver-id="${driver.id}">
                    <div class="d-flex justify-content-between">
                        <div>
                            <h6 class="mb-1">${driver.nombre}</h6>
                            <p class="mb-1">PPU: ${driver.ppu} - ${driver.tipo}</p>
                            <small>Ubicación: ${driver.ubicacion} (${driver.tiempo_ubicacion})</small>
                        </div>
                        <small>Seleccionar</small>
                    </div>
                </button>
            `).join('') + '</div>';
        }

        const modalHtml = `
            <div class="modal fade" id="${modalId}" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Asignar Conductor - ${container.number}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <strong>Contenedor:</strong> ${container.number}<br>
                                <strong>Destino:</strong> ${container.destination}<br>
                                <strong>Programado:</strong> ${container.scheduled_date || ''} ${container.scheduled_time || ''}
                            </div>
                            <h6>Conductores Disponibles</h6>
                            ${bodyHtml}
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const element = document.getElementById(modalId);
        const instance = new bootstrap.Modal(element);
        return { element, instance };
    }

    actions.showAlert = showAlert;

    actions.viewContainer = function (containerId) {
        window.location.href = `/containers/${containerId}/`;
    };

    actions.editContainer = function (containerId) {
        window.open(`/admin/containers/container/${containerId}/change/`, '_blank');
    };

    actions.refreshPage = function () {
        window.location.reload();
    };

    actions.updatePosition = function (containerId, positionCode, options) {
        const settings = Object.assign({
            confirmMessage: positionCode ? `¿Actualizar posición a ${POSITION_LABELS[positionCode] || positionCode}?` : null,
            reload: true,
            delay: 1500
        }, options || {});

        if (!positionCode) {
            showAlert('danger', 'Debe seleccionar una posición válida');
            return Promise.resolve(null);
        }

        if (!confirmAction(settings.confirmMessage)) {
            return Promise.resolve(null);
        }

        return postJson(`/containers/${containerId}/update-position/`, { position: positionCode }).then((data) => {
            if (data.success) {
                showAlert('success', data.message || 'Posición actualizada correctamente');
                if (settings.reload) {
                    reloadAfterDelay(settings.delay);
                }
            } else {
                showAlert('danger', data.message || 'No fue posible actualizar la posición');
            }
            return data;
        }).catch((error) => {
            showAlert('danger', error.message || 'Error al actualizar posición');
            throw error;
        });
    };

    actions.startRoute = function (containerId) {
        return updateStatus(containerId, { status: 'EN_RUTA' }, {
            confirmMessage: '¿Iniciar ruta para este contenedor?',
            successMessage: 'Ruta iniciada exitosamente'
        });
    };

    actions.markArrived = function (containerId, arrivalLocation) {
        if (!arrivalLocation) {
            const modal = createArrivalModal(containerId);
            modal.show();
            return Promise.resolve(null);
        }
        return updateStatus(containerId, { status: 'ARRIBADO', arrival_location: arrivalLocation }, {
            successMessage: 'Arribo registrado correctamente'
        });
    };

    actions.markContainerFinalized = function (containerId, confirmMessage) {
        return updateStatus(containerId, { status: 'FINALIZADO' }, {
            confirmMessage: confirmMessage || '¿Confirmar finalización del contenedor?',
            successMessage: 'Contenedor finalizado exitosamente'
        });
    };

    actions.markContainerEmpty = function (containerId) {
        return actions.markContainerFinalized(containerId, '¿Confirmar que el contenedor está vacío?');
    };

    actions.markContainerFull = function (containerId) {
        return actions.markContainerFinalized(containerId, '¿Confirmar que el contenedor está lleno?');
    };

    actions.quickAssign = function (containerId) {
        if (!confirmAction('¿Asignar automáticamente el mejor conductor disponible?')) {
            return Promise.resolve(null);
        }
        return postJson('/drivers/auto-assign-single/', { container_id: containerId }).then((data) => {
            if (data.success) {
                showAlert('success', data.message || 'Conductor asignado automáticamente');
                reloadAfterDelay(1500);
            } else {
                showAlert('danger', data.message || 'No fue posible realizar la asignación automática');
            }
            return data;
        }).catch((error) => {
            showAlert('danger', error.message || 'Error de conexión al asignar conductor');
            throw error;
        });
    };

    actions.autoAssignAll = function () {
        if (!confirmAction('¿Asignar en automático todos los contenedores programados disponibles?')) {
            return Promise.resolve(null);
        }
        return postJson('/drivers/auto-assign/', {}).then((data) => {
            if (data.success) {
                showAlert('success', data.message || 'Asignación masiva completada');
                reloadAfterDelay(1800);
            } else {
                showAlert('danger', data.message || 'No se pudo auto-asignar a todos los contenedores');
            }
            return data;
        }).catch((error) => {
            showAlert('danger', error.message || 'Error de conexión al auto-asignar');
            throw error;
        });
    };

    actions.assignDriver = function (containerId) {
        fetchWithCsrf(`/drivers/available/?container_id=${containerId}`)
            .then(handleJsonResponse)
            .then((data) => {
                if (!data.success) {
                    showAlert('danger', data.message || 'No fue posible obtener conductores disponibles');
                    return;
                }
                const { element, instance } = renderDriverModal(data.container, data.drivers || []);
                const handler = (event) => {
                    const target = event.target.closest('[data-driver-id]');
                    if (!target) {
                        return;
                    }
                    const driverId = target.getAttribute('data-driver-id');
                    const driverName = target.querySelector('h6') ? target.querySelector('h6').textContent : '';
                    if (!confirmAction(`¿Asignar el conductor ${driverName}?`)) {
                        return;
                    }
                    const formData = new FormData();
                    formData.append('container_id', containerId);
                    formData.append('driver_id', driverId);
                    postForm('/drivers/assign/', formData).then((response) => {
                        if (response.success) {
                            showAlert('success', response.message || 'Conductor asignado correctamente');
                            reloadAfterDelay(1500);
                        } else {
                            showAlert('danger', response.message || 'No fue posible asignar el conductor');
                        }
                    }).catch((error) => {
                        showAlert('danger', error.message || 'Error al asignar conductor');
                    });
                    element.removeEventListener('click', handler);
                    const modalInstance = bootstrap.Modal.getInstance(element);
                    if (modalInstance) {
                        modalInstance.hide();
                    }
                };
                element.addEventListener('click', handler);
                instance.show();
            })
            .catch((error) => showAlert('danger', error.message || 'Error al obtener conductores disponibles'));
    };

    actions.uploadExcelForm = function (form) {
        if (!form) {
            return Promise.resolve(null);
        }
        const endpoint = form.getAttribute('data-upload-endpoint');
        if (!endpoint) {
            showAlert('danger', 'No se definió el endpoint para la carga');
            return Promise.resolve(null);
        }

        const fileInput = form.querySelector('input[type="file"]');
        if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
            showAlert('warning', 'Seleccione al menos un archivo para cargar');
            return Promise.resolve(null);
        }

        const submitButton = form.querySelector('[type="submit"]');
        const originalHtml = submitButton ? submitButton.innerHTML : '';
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Procesando...';
        }

        const formData = new FormData();
        Array.prototype.forEach.call(fileInput.files, (file) => {
            formData.append('files', file);
        });

        const resultContainer = form.nextElementSibling && form.nextElementSibling.classList.contains('upload-result')
            ? form.nextElementSibling
            : null;
        if (resultContainer) {
            resultContainer.innerHTML = '<span class="text-info">Procesando archivos...</span>';
        }

        return postForm(endpoint, formData).then((data) => {
            if (data.summaries && Array.isArray(data.summaries)) {
                const summaryHtml = data.summaries.map((summary) => `
                    <div class="mb-2">
                        <strong>${summary.file_name}</strong>
                        <div class="small text-muted">Creados: ${summary.created} · Actualizados: ${summary.updated} · Omitidos: ${summary.skipped}</div>
                        ${summary.errors && summary.errors.length ? `<div class="small text-danger">Errores: ${summary.errors.join(', ')}</div>` : ''}
                    </div>
                `).join('');
                if (resultContainer) {
                    resultContainer.innerHTML = summaryHtml;
                }
                showAlert('success', 'Importación completada correctamente');
            } else {
                if (resultContainer) {
                    resultContainer.innerHTML = '<span class="text-warning">No se recibió un resumen de importación.</span>';
                }
                showAlert('warning', 'La importación finalizó sin datos de resumen');
            }
        }).catch((error) => {
            if (resultContainer) {
                resultContainer.innerHTML = `<span class="text-danger">${error.message || 'Error al importar archivos'}</span>`;
            }
            showAlert('danger', error.message || 'Error al procesar archivos');
        }).finally(() => {
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = originalHtml;
            }
            if (fileInput) {
                fileInput.value = '';
            }
        });
    };

    actions.registerUploadForms = function () {
        document.querySelectorAll('form[data-upload-endpoint]').forEach((formElement) => {
            if (formElement.getAttribute('data-soptraloc-bound')) {
                return;
            }
            formElement.setAttribute('data-soptraloc-bound', 'true');
            formElement.addEventListener('submit', (event) => {
                event.preventDefault();
                actions.uploadExcelForm(formElement);
            });

            const autoSubmit = formElement.dataset.autoSubmit === 'true';
            const fileInput = formElement.querySelector('input[type="file"]');
            if (autoSubmit && fileInput && !fileInput.dataset.soptralocAutoSubmit) {
                fileInput.dataset.soptralocAutoSubmit = 'true';
                fileInput.addEventListener('change', () => {
                    if (fileInput.files && fileInput.files.length > 0) {
                        formElement.requestSubmit();
                    }
                });
            }
        });
    };

    actions.openUploadDialog = function (selector) {
        const formElement = typeof selector === 'string' ? document.querySelector(selector) : selector;
        if (!formElement) {
            showAlert('danger', 'No se encontró el formulario de carga solicitado.');
            return;
        }

        const fileInput = formElement.querySelector('input[type="file"]');
        if (!fileInput) {
            showAlert('danger', 'El formulario seleccionado no tiene un campo de archivos.');
            return;
        }

        if (formElement.dataset.autoSubmit === 'true' && !fileInput.dataset.soptralocAutoSubmit) {
            fileInput.dataset.soptralocAutoSubmit = 'true';
            fileInput.addEventListener('change', () => {
                if (fileInput.files && fileInput.files.length > 0) {
                    formElement.requestSubmit();
                }
            });
        }

        fileInput.click();
    };

    actions.scheduleAutoRefresh = function (milliseconds) {
        if (!milliseconds || Number(milliseconds) <= 0) {
            return;
        }
        setTimeout(() => {
            window.location.reload();
        }, Number(milliseconds));
    };

    document.addEventListener('DOMContentLoaded', () => {
        ensureCsrfInput();
        actions.registerUploadForms();
    });

    window.SoptralocActions = actions;
})(window, document);
