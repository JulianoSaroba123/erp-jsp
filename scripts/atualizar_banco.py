"""Script to apply Alembic migrations programmatically.
Usage: python scripts/atualizar_banco.py
"""
import os
import sys
from alembic import command
from alembic.config import Config

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE)

def main():
    ini_path = os.path.join(BASE, 'alembic.ini')
    cfg = Config(ini_path)
    cfg.set_main_option('script_location', os.path.join(BASE, 'alembic'))
    print('Applying migrations...')
    command.upgrade(cfg, 'head')
    print('Migrations applied.')

if __name__ == '__main__':
    main()
