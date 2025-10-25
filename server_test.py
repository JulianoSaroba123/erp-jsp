#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.app import create_app

app = create_app()
app.config['DEBUG'] = True

print('🔧 Servidor teste na porta 5002...')
print('📍 URL: http://127.0.0.1:5002')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)