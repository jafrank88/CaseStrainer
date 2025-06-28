import os
import logging
from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

def create_app(config_name=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder='../static/vue')
    
    # Configure logging
    configure_logging(app)
    
    try:
        # Load default configuration
        from config import DefaultConfig, DevelopmentConfig, ProductionConfig
        
        # Set default configuration
        app.config.from_object(DefaultConfig)
        
        # Load environment-specific configuration
        if config_name is None:
            config_name = os.environ.get('FLASK_ENV', 'production')
        
        if config_name == 'development':
            app.config.from_object(DevelopmentConfig)
        elif config_name == 'production':
            app.config.from_object(ProductionConfig)
        
        # Apply any environment variable overrides
        app.config.from_prefixed_env()
        
        # Ensure required directories exist
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Initialize extensions
        initialize_extensions(app)
        
        # Register blueprints
        register_blueprints(app)
        
        # Add middleware
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=1,
            x_proto=1,
            x_host=1,
            x_prefix=1
        )
        
        # Note: Health endpoint removed - use /casestrainer/api/health from vue_api_endpoints.py instead
        
        app.logger.info(f"Application initialized in {app.config['ENV']} mode")
        
    except Exception as e:
        app.logger.error(f"Failed to initialize application: {str(e)}")
        raise
    
    return app

def configure_logging(app):
    """Configure logging for the application."""
    # Use project root logs directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(project_root, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    if app.debug:
        # Detailed logging for development
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(os.path.join(logs_dir, 'casestrainer.log'))
            ]
        )
    else:
        # More concise logging for production
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(os.path.join(logs_dir, 'casestrainer.log'))
            ]
        )
    
    # Set the app's logger level
    app.logger.setLevel(logging.DEBUG if app.debug else logging.INFO)

def initialize_extensions(app):
    """Initialize Flask extensions."""
    # Initialize any extensions here
    pass

def register_blueprints(app):
    """Register Flask blueprints."""
    try:
        from . import routes
        app.register_blueprint(routes.api, url_prefix='/api')
        app.logger.info("Registered API blueprint")
        
        # Register frontend blueprint for serving static files
        app.register_blueprint(routes.frontend)
        app.logger.info("Registered frontend blueprint")
        
    except Exception as e:
        app.logger.error(f"Failed to register blueprints: {str(e)}")
        raise
