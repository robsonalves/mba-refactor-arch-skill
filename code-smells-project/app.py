"""Composition root: wires config, database, routes and middlewares together."""
import logging

from flask import Flask
from flask_cors import CORS

from config import settings
from database import init_db
from middlewares.error_handler import register_error_handlers
from routes import produto_routes, usuario_routes, pedido_routes, system_routes


def create_app():
    logging.basicConfig(
        level=logging.INFO,
        format='{"level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}',
    )

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG

    CORS(app, origins=settings.CORS_ORIGINS)

    init_db(app)

    app.register_blueprint(system_routes.bp)
    app.register_blueprint(produto_routes.bp)
    app.register_blueprint(usuario_routes.bp)
    app.register_blueprint(pedido_routes.bp)

    register_error_handlers(app)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
