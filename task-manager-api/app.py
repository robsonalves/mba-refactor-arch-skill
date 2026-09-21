from flask import Flask
from flask_cors import CORS

from config.settings import Config
from database import db
from middlewares.error_handler import register_error_handlers
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from utils.helpers import now_utc


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)

    # CORS restrito à allowlist da config (nunca '*').
    CORS(app, origins=config.CORS_ORIGINS)
    db.init_app(app)

    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(report_bp)
    register_error_handlers(app)

    @app.route('/health')
    def health():
        return {'status': 'ok', 'timestamp': str(now_utc())}

    @app.route('/')
    def index():
        return {'message': 'Task Manager API', 'version': '1.0'}

    return app


def init_db(app):
    with app.app_context():
        db.create_all()


app = create_app()

if __name__ == '__main__':
    init_db(app)
    app.run(debug=app.config['DEBUG'], host=app.config['HOST'], port=app.config['PORT'])
