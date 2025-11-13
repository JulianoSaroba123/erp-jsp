
// Configuração otimizada da sidebar sem menu de usuário
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Configurando sidebar limpa...');
    
    const sidebar = document.querySelector('.sidebar');
    const sidebarNav = document.querySelector('.sidebar-nav');
    
    if (sidebar) {
        sidebar.style.display = 'flex';
        sidebar.style.flexDirection = 'column';
        sidebar.style.height = '100vh';
        sidebar.style.overflowY = 'hidden';
        sidebar.style.position = 'fixed';
        console.log('✅ Sidebar configurada com layout limpo');
    }
    
    if (sidebarNav) {
        sidebarNav.style.flex = '1';
        sidebarNav.style.overflowY = 'auto';
        sidebarNav.style.overflowX = 'hidden';
        sidebarNav.style.paddingBottom = '20px';
        console.log('✅ Navegação da sidebar configurada para scroll');
    }
    
    // Verificar itens de menu
    const menuItems = document.querySelectorAll('.nav-item');
    if (menuItems.length > 0) {
        console.log(`📋 ${menuItems.length} itens de menu encontrados`);
    }
    
    console.log('✅ Sidebar limpa configurada com sucesso!');
});

// Reset quando a página for totalmente carregada
window.addEventListener('load', function() {
    const sidebarNav = document.querySelector('.sidebar-nav');
    if (sidebarNav) {
        sidebarNav.scrollTop = 0;
        console.log('🔄 Posição de scroll resetada');
    }
});
