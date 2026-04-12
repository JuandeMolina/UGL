/*
 * Service Worker for UGL Push Notifications
 */
self.addEventListener('push', function (event) {
    const data = event.data ? event.data.json() : { title: 'UGL', body: 'Nueva actualización' };

    const options = {
        body: data.body,
        icon: '/static/favicon.png',
        badge: '/static/favicon.png',
        data: { url: data.url }
    };

    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

self.addEventListener('notificationclick', function (event) {
    event.notification.close();
    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});