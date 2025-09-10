import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aplicacao import create_app

app = create_app()
with app.app_context():
    app.jinja_env.globals['current_app'] = app
    from flask import url_for
    with app.test_request_context('/'):
        tpl = app.jinja_env.get_template('painel/painel.html')
        print('--- RENDER START ---')
        print(tpl.render())
        print('--- RENDER END ---')
