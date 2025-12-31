// PWA Installation Handler para ERP JSP
// Gerencia a instalação do app e registro do Service Worker

let deferredPrompt;
let isInstalled = false;

// Registra o Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/static/service-worker.js')
      .then((registration) => {
        console.log('✅ Service Worker registrado com sucesso:', registration.scope);
        
        // Verifica atualizações a cada hora
        setInterval(() => {
          registration.update();
        }, 60 * 60 * 1000);
      })
      .catch((error) => {
        console.error('❌ Erro ao registrar Service Worker:', error);
      });
  });
}

// Detecta quando o app pode ser instalado
window.addEventListener('beforeinstallprompt', (e) => {
  console.log('💾 App pronto para instalação');
  
  // Previne o prompt automático
  e.preventDefault();
  
  // Armazena o evento para uso posterior
  deferredPrompt = e;
  
  // Mostra o botão de instalação customizado
  showInstallPromotion();
});

// Detecta quando o app foi instalado
window.addEventListener('appinstalled', (evt) => {
  console.log('✅ App instalado com sucesso!');
  isInstalled = true;
  hideInstallPromotion();
  
  // Analytics opcional
  if (typeof gtag !== 'undefined') {
    gtag('event', 'app_installed', {
      event_category: 'pwa',
      event_label: 'ERP JSP PWA Instalado'
    });
  }
});

// Mostra banner de instalação
function showInstallPromotion() {
  const installBanner = document.getElementById('install-banner');
  if (installBanner) {
    installBanner.style.display = 'block';
  } else {
    createInstallBanner();
  }
}

// Esconde banner de instalação
function hideInstallPromotion() {
  const installBanner = document.getElementById('install-banner');
  if (installBanner) {
    installBanner.style.display = 'none';
  }
}

// Cria banner de instalação customizado
function createInstallBanner() {
  const banner = document.createElement('div');
  banner.id = 'install-banner';
  banner.style.cssText = `
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
    color: white;
    padding: 15px 25px;
    border-radius: 50px;
    box-shadow: 0 4px 20px rgba(6, 182, 212, 0.4);
    display: flex;
    align-items: center;
    gap: 15px;
    z-index: 9999;
    animation: slideUp 0.3s ease-out;
    max-width: 90%;
  `;
  
  banner.innerHTML = `
    <style>
      @keyframes slideUp {
        from {
          transform: translateX(-50%) translateY(100px);
          opacity: 0;
        }
        to {
          transform: translateX(-50%) translateY(0);
          opacity: 1;
        }
      }
      
      @media (max-width: 768px) {
        #install-banner {
          flex-direction: column;
          text-align: center;
          padding: 20px;
        }
        #install-banner button {
          width: 100%;
          margin-top: 10px;
        }
      }
    </style>
    <div style="flex: 1;">
      <strong style="display: block; margin-bottom: 5px;">📱 Instalar ERP JSP</strong>
      <small style="opacity: 0.9;">Adicione à tela inicial para acesso rápido</small>
    </div>
    <button onclick="installApp()" style="
      background: white;
      color: #06b6d4;
      border: none;
      padding: 10px 25px;
      border-radius: 25px;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.2s;
      white-space: nowrap;
    " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
      Instalar Agora
    </button>
    <button onclick="hideInstallPromotion()" style="
      background: transparent;
      color: white;
      border: none;
      padding: 10px;
      cursor: pointer;
      font-size: 20px;
      line-height: 1;
    " title="Fechar">
      ×
    </button>
  `;
  
  document.body.appendChild(banner);
}

// Função para instalar o app
async function installApp() {
  if (!deferredPrompt) {
    console.log('⚠️ Prompt de instalação não disponível');
    return;
  }
  
  // Mostra o prompt de instalação
  deferredPrompt.prompt();
  
  // Aguarda a escolha do usuário
  const { outcome } = await deferredPrompt.userChoice;
  
  console.log(`👤 Usuário ${outcome === 'accepted' ? 'aceitou' : 'recusou'} a instalação`);
  
  if (outcome === 'accepted') {
    hideInstallPromotion();
  }
  
  // Limpa o prompt
  deferredPrompt = null;
}

// Verifica se o app já está instalado
function checkIfInstalled() {
  // Para iOS Safari
  if (window.navigator.standalone === true) {
    isInstalled = true;
    console.log('✅ App rodando como standalone (iOS)');
  }
  
  // Para outros navegadores
  if (window.matchMedia('(display-mode: standalone)').matches) {
    isInstalled = true;
    console.log('✅ App rodando em modo standalone');
  }
  
  // Para Android/Chrome
  if (document.referrer.includes('android-app://')) {
    isInstalled = true;
    console.log('✅ App rodando via TWA (Android)');
  }
  
  return isInstalled;
}

// Mostra notificação de update disponível
function showUpdateNotification() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready.then((registration) => {
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            // Nova versão disponível
            if (confirm('🎉 Nova versão do ERP JSP disponível! Deseja atualizar agora?')) {
              newWorker.postMessage({ action: 'skipWaiting' });
              window.location.reload();
            }
          }
        });
      });
    });
  }
}

// Suporte a notificações push
async function requestNotificationPermission() {
  if (!('Notification' in window)) {
    console.log('⚠️ Este navegador não suporta notificações');
    return false;
  }
  
  if (Notification.permission === 'granted') {
    console.log('✅ Permissão de notificação já concedida');
    return true;
  }
  
  if (Notification.permission !== 'denied') {
    const permission = await Notification.requestPermission();
    if (permission === 'granted') {
      console.log('✅ Permissão de notificação concedida');
      return true;
    }
  }
  
  console.log('❌ Permissão de notificação negada');
  return false;
}

// Envia notificação de teste
function sendTestNotification() {
  if (Notification.permission === 'granted') {
    navigator.serviceWorker.ready.then((registration) => {
      registration.showNotification('ERP JSP', {
        body: 'Notificações ativadas com sucesso! 🎉',
        icon: '/static/icons/icon-192.png',
        badge: '/static/icons/icon-96.png',
        vibrate: [200, 100, 200]
      });
    });
  }
}

// Inicializa quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
  checkIfInstalled();
  showUpdateNotification();
  
  // Se já estiver instalado, não mostra o banner
  if (!isInstalled && !sessionStorage.getItem('installBannerDismissed')) {
    // Aguarda 10 segundos antes de mostrar o banner
    setTimeout(() => {
      if (deferredPrompt) {
        showInstallPromotion();
      }
    }, 10000);
  }
});

// Detecta mudanças no modo de exibição
window.matchMedia('(display-mode: standalone)').addEventListener('change', (evt) => {
  if (evt.matches) {
    console.log('✅ App agora em modo standalone');
    isInstalled = true;
  } else {
    console.log('ℹ️ App não está em modo standalone');
  }
});

// Exporta funções para uso global
window.pwaInstall = {
  install: installApp,
  checkIfInstalled,
  requestNotificationPermission,
  sendTestNotification
};
