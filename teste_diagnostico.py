# -*- coding: utf-8 -*-
"""
Testa endpoint de diagnóstico
"""
import requests

url = "https://erp-jsp-th5o.onrender.com/diagnostico/status"

try:
    response = requests.get(url, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        import json
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(response.text)
except Exception as e:
    print(f"Erro: {e}")
