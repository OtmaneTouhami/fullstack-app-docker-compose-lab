import os

import redis
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from redis.exceptions import RedisError
from sqlalchemy import text

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is required")

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}

    # Redis connection for caching
    app.redis = redis.Redis(
        host=os.getenv("REDIS_HOST", "cache"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=0,
        decode_responses=True,
    )

    db.init_app(app)

    @app.before_request
    def ensure_tables_exist():
        if getattr(app, "_tables_created", False):
            return
        db.create_all()
        app._tables_created = True

    @app.route("/health", methods=["GET"])
    def health():
        status = {"app": "ok"}
        ok = True

        try:
            db.session.execute(text("SELECT 1"))
            status["database"] = "ok"
        except Exception as exc:  # pragma: no cover - best-effort diagnostics
            status["database"] = f"error: {exc}"
            ok = False

        try:
            app.redis.ping()
            status["cache"] = "ok"
        except RedisError as exc:  # pragma: no cover - best-effort diagnostics
            status["cache"] = f"error: {exc}"
            ok = False

        return jsonify(status), 200 if ok else 503

    from .routes import users_bp

    app.register_blueprint(users_bp)

    return app
