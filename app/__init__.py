"""
Main Flask Application
Privacy-Preserving AI Chatbot
"""

from flask import Flask
from flask_cors import CORS
from app.routes import main_bp
import os


def create_app():
    """
    Application factory for creating Flask app
    
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['JSON_SORT_KEYS'] = False
    
    # Enable CORS for API endpoints
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Register blueprints
    app.register_blueprint(main_bp)
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
