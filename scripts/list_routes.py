import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aplicacao import create_app

app = create_app()
print('Blueprints:', list(app.blueprints.keys()))
print('Routes:')
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint:40} -> {rule}")
