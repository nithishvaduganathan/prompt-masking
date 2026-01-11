"""
Main entry point for the Flask application
"""

from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    # Only enable debug mode if explicitly set in environment (default: False for security)
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
