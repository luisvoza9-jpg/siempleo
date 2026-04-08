self.addEventListener('install', (e) => {
  console.log('[Service Worker] Instalado correctamente');
});

self.addEventListener('fetch', (e) => {
  // El navegador solo pide que esto exista para dejarte instalar la app
});

