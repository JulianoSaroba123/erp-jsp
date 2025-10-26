#!/usr/bin/env python3
"""
Alternative startup script for Render deployment
"""
import os
import sys

# Ensure the current directory is in the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Try to import and run the app
try:
    from wsgi import app
    
    if __name__ == "__main__":
        port = int(os.environ.get("PORT", 10000))
        app.run(host="0.0.0.0", port=port, debug=False)
        
except ImportError:
    # Fallback - try direct import
    try:
        from app.app import create_app
        
        app = create_app('production')
        
        # Initialize database
        with app.app_context():
            try:
                from app.extensoes import db
                db.create_all()
                print("✅ Database initialized")
            except Exception as e:
                print(f"⚠️ Database warning: {e}")
        
        if __name__ == "__main__":
            port = int(os.environ.get("PORT", 10000))
            app.run(host="0.0.0.0", port=port, debug=False)
            
    except Exception as e:
        print(f"❌ Startup error: {e}")
        sys.exit(1)