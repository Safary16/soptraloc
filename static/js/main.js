// SoptraLoc TMS - Main JavaScript
//
// Utilidades comunes disponibles globalmente via window.SoptralocUtils.
// Se evito sobreescribir e/esc/getCookie en el scope global para no
// colisionar con las definiciones inline de los templates que aun las usan
// (asignacion, monitoreo, etc). Para nuevo codigo se prefiere:
//   SoptralocUtils.e('<html>')      // escape HTML
//   SoptralocUtils.esc(s)           // alias de e()
//   SoptralocUtils.getCookie('csrfmiddlewaretoken')

(function () {
    'use strict';

    // Real-time clock (existente, se mantiene para compatibilidad).
    function updateClock() {
        const el = document.getElementById('realtime-clock');
        if (el) {
            el.textContent = new Date().toLocaleDateString('es-CL', {
                weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
                hour: '2-digit', minute: '2-digit', second: '2-digit'
            });
        }
    }
    setInterval(updateClock, 1000);

    // ------------------------------------------------------------------
    // Utilidades centralizadas (Group 22 — auditoría 2026-09-25)
    // ------------------------------------------------------------------

    /**
     * Escape HTML para evitar XSS al inyectar strings en innerHTML.
     * Misma semantica que las versiones inline que tenian los templates.
     */
    function e(s) {
        if (s === null || s === undefined) return '';
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    /** Alias semantico de e(). */
    function esc(s) {
        return e(s);
    }

    /**
     * Lee una cookie por nombre. Util para CSRF en llamadas fetch.
     */
    function getCookie(name) {
        if (!name) return null;
        const match = document.cookie.match(new RegExp('(^|; )' + name + '=([^;]*)'));
        return match ? decodeURIComponent(match[2]) : null;
    }

    /**
     * Wrapper post() con CSRF + JSON consistente para todas las vistas
     * que aún no usan fetch directo. Devuelve Promise<Response>.
     */
    function post(url, data) {
        const csrf = getCookie('csrftoken');
        const body = data instanceof FormData ? data : JSON.stringify(data || {});
        const headers = {
            'X-CSRFToken': csrf || '',
            'X-Requested-With': 'XMLHttpRequest',
        };
        if (!(data instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
        }
        return fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: headers,
            body: body,
        });
    }

    // Namespace publico (no se exporta al scope global plano para no chocar
    // con las definiciones inline de los templates).
    window.SoptralocUtils = {
        e: e,
        esc: esc,
        getCookie: getCookie,
        post: post,
        // Alias historico para retrocompatibilidad con cualquier codigo que
        // ya estuviera leyendo SoptralocUtils |Soptraloc|.
        Soptraloc: { post: post, getCookie: getCookie, e: e, esc: esc },
    };
})();
