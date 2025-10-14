/**
 * Service Worker para SoptraLoc Driver
 * Permite GPS tracking en background sin mantener la app abierta
 * Cumple con requisitos legales: conductor no necesita celular desbloqueado
 */

const CACHE_NAME = 'soptraloc-v1';
const GPS_SYNC_TAG = 'sync-gps-location';

// Archivos a cachear para funcionamiento offline
const urlsToCache = [
    '/driver/dashboard/',
    '/static/css/ubuntu-style.css',
    '/static/js/main.js',
    '/static/img/icon-192.png'
];

/**
 * Instalación del Service Worker
 */
self.addEventListener('install', (event) => {
    console.log('[SW] Instalando Service Worker...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[SW] Cacheando archivos');
                return cache.addAll(urlsToCache);
            })
            .then(() => self.skipWaiting())
    );
});

/**
 * Activación del Service Worker
 */
self.addEventListener('activate', (event) => {
    console.log('[SW] Activando Service Worker...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('[SW] Eliminando cache antiguo:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    return self.clients.claim();
});

/**
 * Intercepción de requests (estrategia: Network First, fallback a Cache)
 */
self.addEventListener('fetch', (event) => {
    event.respondWith(
        fetch(event.request)
            .then((response) => {
                // Clonar response para guardar en cache
                const responseClone = response.clone();
                caches.open(CACHE_NAME).then((cache) => {
                    cache.put(event.request, responseClone);
                });
                return response;
            })
            .catch(() => {
                // Si falla la red, usar cache
                return caches.match(event.request);
            })
    );
});

/**
 * Background Sync para GPS
 * Se ejecuta incluso con app cerrada o pantalla bloqueada
 */
self.addEventListener('sync', (event) => {
    console.log('[SW] Background Sync triggered:', event.tag);
    
    if (event.tag === GPS_SYNC_TAG) {
        event.waitUntil(syncGPSLocation());
    }
});

/**
 * Sincronizar ubicación GPS con el servidor
 */
async function syncGPSLocation() {
    try {
        console.log('[SW] Sincronizando ubicación GPS...');
        
        // Obtener driver ID del IndexedDB o localStorage
        const driverData = await getDriverData();
        
        if (!driverData || !driverData.id) {
            console.warn('[SW] No hay driver ID almacenado');
            return;
        }
        
        // Obtener ubicación GPS
        const position = await getCurrentPosition();
        
        // Enviar al servidor
        const response = await fetch(`/api/drivers/${driverData.id}/track_location/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                lat: position.coords.latitude,
                lng: position.coords.longitude,
                accuracy: position.coords.accuracy,
                timestamp: new Date().toISOString(),
                background: true // Indica que viene del service worker
            })
        });
        
        if (response.ok) {
            console.log('[SW] ✅ Ubicación sincronizada');
            
            // Notificar a las ventanas abiertas
            const clients = await self.clients.matchAll();
            clients.forEach(client => {
                client.postMessage({
                    type: 'GPS_SYNCED',
                    position: {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude
                    }
                });
            });
        } else {
            console.error('[SW] ❌ Error al sincronizar:', response.status);
        }
        
    } catch (error) {
        console.error('[SW] Error en syncGPSLocation:', error);
        throw error; // Re-throw para que Background Sync lo reintente
    }
}

/**
 * Obtener datos del driver desde IndexedDB
 */
async function getDriverData() {
    // En una implementación completa, usar IndexedDB
    // Por simplicidad, usar cache API
    try {
        const cache = await caches.open(CACHE_NAME);
        const response = await cache.match('/driver/data.json');
        if (response) {
            return await response.json();
        }
    } catch (error) {
        console.error('[SW] Error obteniendo driver data:', error);
    }
    return null;
}

/**
 * Obtener posición GPS (Promise wrapper)
 */
function getCurrentPosition() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error('Geolocation not supported'));
            return;
        }
        
        navigator.geolocation.getCurrentPosition(
            resolve,
            reject,
            {
                enableHighAccuracy: false, // Menor precisión = menor batería
                timeout: 10000,
                maximumAge: 30000 // Usar ubicación cacheada de hasta 30s
            }
        );
    });
}

/**
 * Push Notifications
 * Para notificar al conductor de nuevas entregas
 */
self.addEventListener('push', (event) => {
    console.log('[SW] Push notification recibida');
    
    let data = {
        title: 'SoptraLoc',
        body: 'Nueva notificación',
        icon: '/static/img/icon-192.png',
        badge: '/static/img/badge.png'
    };
    
    if (event.data) {
        try {
            data = event.data.json();
        } catch (e) {
            data.body = event.data.text();
        }
    }
    
    const options = {
        body: data.body,
        icon: data.icon || '/static/img/icon-192.png',
        badge: data.badge || '/static/img/badge.png',
        vibrate: [200, 100, 200],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: data.id || 1
        },
        actions: [
            {
                action: 'view',
                title: 'Ver Detalles',
                icon: '/static/img/view-icon.png'
            },
            {
                action: 'close',
                title: 'Cerrar',
                icon: '/static/img/close-icon.png'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

/**
 * Manejo de clicks en notificaciones
 */
self.addEventListener('notificationclick', (event) => {
    console.log('[SW] Notification clicked:', event.action);
    
    event.notification.close();
    
    if (event.action === 'view') {
        // Abrir la app en el dashboard
        event.waitUntil(
            clients.openWindow('/driver/dashboard/')
        );
    }
});

/**
 * Periodic Background Sync (si está disponible)
 * Permite sincronización periódica incluso sin interacción del usuario
 */
self.addEventListener('periodicsync', (event) => {
    console.log('[SW] Periodic sync:', event.tag);
    
    if (event.tag === 'sync-gps-periodic') {
        event.waitUntil(syncGPSLocation());
    }
});

console.log('[SW] Service Worker cargado correctamente');
