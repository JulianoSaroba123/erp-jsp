// Service Worker para ERP JSP - PWA
// Versão: 1.0.0

const CACHE_NAME = 'erp-jsp-v1.0.0';
const OFFLINE_URL = '/offline.html';

// Recursos essenciais para funcionar offline
const ESSENTIAL_RESOURCES = [
  '/',
  '/static/css/bootstrap.min.css',
  '/static/js/bootstrap.bundle.min.js',
  '/static/manifest.json',
  OFFLINE_URL
];

// Instalação do Service Worker
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Instalando...');
  
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[Service Worker] Fazendo cache dos recursos essenciais');
      return cache.addAll(ESSENTIAL_RESOURCES).catch((error) => {
        console.error('[Service Worker] Erro ao fazer cache:', error);
      });
    })
  );
  
  // Força a ativação imediata
  self.skipWaiting();
});

// Ativação do Service Worker
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Ativando...');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('[Service Worker] Removendo cache antigo:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  
  // Toma controle de todas as páginas abertas
  return self.clients.claim();
});

// Interceptação de requisições - Estratégia Network First
self.addEventListener('fetch', (event) => {
  // Ignora requisições que não são GET
  if (event.request.method !== 'GET') {
    return;
  }

  // Ignora requisições para outros domínios
  if (!event.request.url.startsWith(self.location.origin)) {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Se a resposta é válida, clona e armazena no cache
        if (response && response.status === 200) {
          const responseToCache = response.clone();
          
          caches.open(CACHE_NAME).then((cache) => {
            // Não fazer cache de páginas de API ou admin
            if (!event.request.url.includes('/api/') && 
                !event.request.url.includes('/admin/')) {
              cache.put(event.request, responseToCache);
            }
          });
        }
        
        return response;
      })
      .catch(() => {
        // Se falhar, tenta buscar do cache
        return caches.match(event.request).then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          
          // Se não encontrou no cache e é uma página HTML, retorna página offline
          if (event.request.headers.get('accept').includes('text/html')) {
            return caches.match(OFFLINE_URL);
          }
          
          // Para outros recursos, retorna resposta vazia
          return new Response('Recurso não disponível offline', {
            status: 503,
            statusText: 'Service Unavailable',
            headers: new Headers({
              'Content-Type': 'text/plain'
            })
          });
        });
      })
  );
});

// Sincronização em background (quando voltar online)
self.addEventListener('sync', (event) => {
  console.log('[Service Worker] Sincronizando em background...');
  
  if (event.tag === 'sync-data') {
    event.waitUntil(syncData());
  }
});

// Notificações Push
self.addEventListener('push', (event) => {
  console.log('[Service Worker] Push recebido:', event);
  
  const options = {
    body: event.data ? event.data.text() : 'Nova notificação do ERP JSP',
    icon: '/static/icons/icon-192.png',
    badge: '/static/icons/icon-96.png',
    vibrate: [200, 100, 200],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'Ver Detalhes'
      },
      {
        action: 'close',
        title: 'Fechar'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('ERP JSP', options)
  );
});

// Clique em notificação
self.addEventListener('notificationclick', (event) => {
  console.log('[Service Worker] Notificação clicada:', event);
  
  event.notification.close();
  
  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Função auxiliar para sincronizar dados
async function syncData() {
  try {
    // Aqui você pode adicionar lógica para sincronizar dados pendentes
    console.log('[Service Worker] Sincronização de dados completa');
    return Promise.resolve();
  } catch (error) {
    console.error('[Service Worker] Erro na sincronização:', error);
    return Promise.reject(error);
  }
}
