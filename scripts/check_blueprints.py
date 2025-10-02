import traceback
import os
import sys

# Ensure project root is on sys.path so 'aplicacao' package can be imported
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from aplicacao import create_app
    app = create_app()
    
    print("Registered blueprints:")
    for blueprint in app.blueprints:
        print(f"  - {blueprint}")
        bp = app.blueprints[blueprint]
        print(f"    URL prefix: {bp.url_prefix}")
        for rule in app.url_map.iter_rules():
            if rule.endpoint.startswith(blueprint):
                print(f"    Route: {rule.rule} -> {rule.endpoint}")

except Exception as e:
    print('EXCEPTION during app import/initialization:')
    traceback.print_exc()