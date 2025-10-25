#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WSGI Entry Point for Render Deployment
======================================

Simple WSGI entry point for Gunicorn deployment on Render.
This file is used by Gunicorn to start the Flask application.

Usage:
    gunicorn wsgi:app
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the Flask app
from app.app import create_app

# Create the application instance
app = create_app('production')

# Initialize database tables if needed
with app.app_context():
    try:
        from app.extensoes import db
        # Only create tables, don't try to populate with example data
        db.create_all()
        print("✅ Database tables verified/created successfully!")
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")
        # Don't fail the deployment if DB isn't ready yet

if __name__ == "__main__":
    # This is for local testing only
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)