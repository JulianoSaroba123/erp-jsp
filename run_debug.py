# -*- coding: utf-8 -*-
"""Run server com captura completa de erros."""

import sys
import os

# Redireciona stderr para arquivo
error_log = open('startup_error.log', 'w', encoding='utf-8')
sys.stderr = error_log
sys.stdout = error_log

try:
    print("="*60)
    print("INICIANDO SERVIDOR COM CAPTURA DE ERROS")
    print("="*60)
    
    from app.app import app
    
    print("✓ App importado")
    print(f"✓ Debug mode: {app.debug}")
    print(f"✓ Config: {app.config.get('DEBUG')}")
    
    print("\nIniciando servidor...")
    app.run(
        host='127.0.0.1',
        port=5001,
        debug=True,
        use_reloader=False
    )
    
except Exception as e:
    print(f"\n{'='*60}")
    print(f"ERRO FATAL: {e}")
    print(f"{'='*60}")
    import traceback
    traceback.print_exc()
finally:
    error_log.close()
