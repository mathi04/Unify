from flask import Flask
from .config import Config
from .extensions import db, login_manager
from .auth import auth_bp
from .main import main_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(main_bp)

    from .cli import register_cli
    register_cli(app)

    return app
