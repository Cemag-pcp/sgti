// Service Worker - SGTI notificacoes de chamados

self.addEventListener('push', function (event) {
  let payload = {
    title: 'Novo chamado',
    body: 'Um novo chamado foi aberto.',
    tag: 'ticket-notification',
    url: '/tickets/',
  };

  if (event.data) {
    try {
      payload = Object.assign(payload, event.data.json());
    } catch (error) {
      payload.body = event.data.text();
    }
  }

  event.waitUntil(
    self.registration.showNotification(payload.title, {
      body: payload.body,
      tag: payload.tag,
      data: { url: payload.url },
    }).then(function () {
      return self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    }).then(function (windowClients) {
      windowClients.forEach(function (client) {
        client.postMessage({ type: 'NEW_TICKET_SOUND' });
      });
    })
  );
});

self.addEventListener('notificationclick', function (event) {
  event.notification.close();
  const url = event.notification.data && event.notification.data.url;
  if (!url) return;
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (windowClients) {
      for (const client of windowClients) {
        if (client.url.includes(url) && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(url);
      }
    })
  );
});
