
// Configuração otimizada da sidebar sem menu de usuário
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.sidebar');
    const sidebarNav = document.querySelector('.sidebar-nav');
    
    if (sidebar) {
        sidebar.style.display = 'flex';
        sidebar.style.flexDirection = 'column';
        sidebar.style.height = '100vh';
        sidebar.style.overflowY = 'hidden';
        sidebar.style.position = 'fixed';
    }
    
    if (sidebarNav) {
        sidebarNav.style.flex = '1';
        sidebarNav.style.overflowY = 'auto';
        sidebarNav.style.overflowX = 'hidden';
        sidebarNav.style.paddingBottom = '20px';
    }
});

// Reset quando a página for totalmente carregada
window.addEventListener('load', function() {
    const sidebarNav = document.querySelector('.sidebar-nav');
    if (sidebarNav) {
        sidebarNav.scrollTop = 0;
    }
});
