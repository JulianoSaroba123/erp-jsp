import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aplicacao import create_app

app = create_app()
with app.app_context():
    # Make current_app available to templates when rendering in tests
    app.jinja_env.globals['current_app'] = app
    tpl = app.jinja_env.get_template('includes/menu_lateral.html')
    # Use a test_request_context so url_for works during template rendering
    with app.test_request_context('/'):
        rendered = tpl.render()
        print('--- RENDER START ---')
        print(rendered)
        print('--- RENDER END ---')
