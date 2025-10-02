#!/usr/bin/env python3
"""
Script para debugar rotas registradas no Flask
"""

from aplicacao import create_app

def listar_rotas():
    app = create_app()
    
    print("=== ROTAS REGISTRADAS ===")
    
    with app.app_context():
        for rule in app.url_map.iter_rules():
            print(f"Endpoint: {rule.endpoint:30} | URL: {rule.rule:30} | Métodos: {list(rule.methods)}")
    
    print("\n=== BLUEPRINTS REGISTRADOS ===")
    for blueprint_name in app.blueprints:
        print(f"Blueprint: {blueprint_name}")

if __name__ == "__main__":
    listar_rotas()