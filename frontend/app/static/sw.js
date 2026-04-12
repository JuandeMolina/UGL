/*
 * Service Worker for UGL Push Notifications
 */

self.addEventListener('push', function(event) {
    console.log('[Service Worker] Push Received.');
    console.log(`[Service Worker] Push had this data: "${event.data.text()}"`);

    let data = { title: 'UGL', body: 'Nueva notificación', url: '/' };
    try {
        data = event.data.json();
    } catch (e) {
        data.body = event.data.text();
    }

    const title = data.title || 'UGL';
    const options = {
        body: data.body,
        icon: '/static/icons/icon-192x192.png', // Opcional: añadir icono real luego
        badge: '/static/icons/badge-72x72.png',
        data: {
            url: data.url || '/'
        }
    };

    event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', function(event) {
    console.log('[Service Worker] Notification click Received.');
    event.notification.close();

    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});
