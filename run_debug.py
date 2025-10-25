from app.app import create_app
import requests
import time

app = create_app()
app.config['DEBUG'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True

if __name__ == '__main__':
    # Start the app in debug mode (reloader off to keep single process)
    print('Starting debug server on http://127.0.0.1:5001 ...')
    from threading import Thread
    def run_server():
        app.run(host='127.0.0.1', port=5001, debug=True, use_reloader=False)

    t = Thread(target=run_server, daemon=True)
    t.start()

    # Wait a bit for server to start
    time.sleep(1.5)

    try:
        resp = requests.get('http://127.0.0.1:5001/ordem_servico/2/editar', timeout=10)
        print('STATUS', resp.status_code)
        print(resp.text[:4000])
    except Exception as e:
        print('Request error:', e)

    # Keep process alive briefly so user can reproduce in browser if needed
    time.sleep(2)
