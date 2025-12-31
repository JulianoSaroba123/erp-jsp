#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de PWA - ERP JSP
=======================

Verifica se todos os componentes PWA estão configurados corretamente.
"""

import os
import json

def check_file_exists(path, description):
    """Verifica se um arquivo existe."""
    exists = os.path.exists(path)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {path}")
    return exists

def check_manifest():
    """Verifica o manifest.json."""
    manifest_path = os.path.join('app', 'static', 'manifest.json')
    
    if not os.path.exists(manifest_path):
        print("❌ manifest.json não encontrado!")
        return False
    
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        # Verifica campos obrigatórios
        required_fields = ['name', 'short_name', 'start_url', 'display', 'icons']
        missing = [field for field in required_fields if field not in manifest]
        
        if missing:
            print(f"❌ Campos faltando no manifest: {', '.join(missing)}")
            return False
        
        # Verifica ícones
        if len(manifest['icons']) < 2:
            print("⚠️ Recomendado ter pelo menos 2 ícones (192x192 e 512x512)")
        
        print(f"✅ manifest.json válido com {len(manifest['icons'])} ícones")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao ler manifest.json: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def check_icons():
    """Verifica se os ícones existem."""
    icons_dir = os.path.join('app', 'static', 'icons')
    required_sizes = [192, 512]
    
    if not os.path.exists(icons_dir):
        print(f"❌ Diretório de ícones não encontrado: {icons_dir}")
        return False
    
    missing = []
    for size in required_sizes:
        icon_path = os.path.join(icons_dir, f'icon-{size}.png')
        if not os.path.exists(icon_path):
            missing.append(size)
    
    if missing:
        print(f"⚠️ Ícones faltando: {', '.join(str(s) for s in missing)}x{missing[0]}")
        return False
    
    # Conta todos os ícones
    icons = [f for f in os.listdir(icons_dir) if f.endswith('.png')]
    print(f"✅ {len(icons)} ícones encontrados em {icons_dir}")
    return True

def main():
    """Executa todos os testes."""
    print("="*60)
    print("🧪 Teste de Configuração PWA - ERP JSP")
    print("="*60 + "\n")
    
    results = []
    
    # 1. Verifica arquivos base
    print("📁 Verificando arquivos base...")
    results.append(check_file_exists('app/static/manifest.json', 'Manifest PWA'))
    results.append(check_file_exists('app/static/service-worker.js', 'Service Worker'))
    results.append(check_file_exists('app/static/js/pwa-install.js', 'Script de Instalação'))
    results.append(check_file_exists('app/templates/offline.html', 'Página Offline'))
    print()
    
    # 2. Verifica manifest
    print("📋 Validando manifest.json...")
    results.append(check_manifest())
    print()
    
    # 3. Verifica ícones
    print("🎨 Verificando ícones...")
    results.append(check_icons())
    print()
    
    # 4. Verifica base.html
    print("🔗 Verificando integração no base.html...")
    base_html_path = 'app/templates/base.html'
    if os.path.exists(base_html_path):
        with open(base_html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        checks = [
            ('manifest', 'manifest.json' in content),
            ('theme-color', 'theme-color' in content),
            ('apple-mobile-web-app', 'apple-mobile-web-app-capable' in content),
            ('pwa-install.js', 'pwa-install.js' in content)
        ]
        
        for name, check in checks:
            status = "✅" if check else "❌"
            print(f"{status} {name}")
            results.append(check)
    else:
        print("❌ base.html não encontrado")
        results.append(False)
    
    print()
    
    # Resultado final
    print("="*60)
    passed = sum(results)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    if percentage == 100:
        print(f"🎉 SUCESSO! Todos os {total} testes passaram!")
        print("\n✨ O PWA está configurado corretamente!")
        print("\n📱 Próximos passos:")
        print("   1. Execute o servidor: python run.py")
        print("   2. Acesse via HTTPS (use ngrok ou configure SSL)")
        print("   3. Teste a instalação no navegador")
        print("   4. Execute Lighthouse para auditoria completa")
    elif percentage >= 80:
        print(f"⚠️ ATENÇÃO: {passed}/{total} testes passaram ({percentage:.1f}%)")
        print("\n🔧 Alguns componentes precisam de atenção.")
    else:
        print(f"❌ FALHA: Apenas {passed}/{total} testes passaram ({percentage:.1f}%)")
        print("\n🔧 Configure os componentes faltantes:")
        print("   - Execute: python gerar_icones_pwa.py")
        print("   - Verifique o GUIA_PWA.md para instruções")
    
    print("="*60)

if __name__ == '__main__':
    main()
