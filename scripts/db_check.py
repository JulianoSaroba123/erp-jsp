import os
import sqlite3
import getpass
import sys

DB = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database', 'database.db'))
print('DB:', DB)
print('exists:', os.path.exists(DB))
print('isfile:', os.path.isfile(DB))
print('isdir:', os.path.isdir(DB))
print('cwd:', os.getcwd())
print('user:', getpass.getuser())
if os.path.exists(DB):
    st = os.stat(DB)
    print('mode:', oct(st.st_mode))
    print('size:', st.st_size)
    print('writable:', os.access(DB, os.W_OK))
    print('readable:', os.access(DB, os.R_OK))

try:
    conn = sqlite3.connect(DB)
    conn.execute('SELECT 1')
    conn.close()
    print('sqlite connect: OK')
except Exception as e:
    print('sqlite connect error:', type(e).__name__, e)
    sys.exit(1)

sys.exit(0)
