import sys, os
sys.path.insert(0, os.path.abspath('.'))
from aplicacao import create_app
app = create_app()
with app.app_context():
    tpl = app.jinja_env.get_template('includes/menu_lateral.html')
    print('Rendered length:', len(tpl.render()))
