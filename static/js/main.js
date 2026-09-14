// SoptraLoc TMS - Main JavaScript

// Real-time clock
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
