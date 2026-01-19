from flask import Flask
from .config import Config
from .extensions import db, login_manager
from .auth import auth_bp
from .main import main_bp
from .courses import courses_bp
from .events import events_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(main_bp)
    app.register_blueprint(courses_bp, url_prefix="/courses")
    app.register_blueprint(events_bp, url_prefix="/events")

    from .cli import register_cli
    register_cli(app)

    return app
