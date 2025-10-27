import json

from flask import Blueprint, current_app, jsonify, request
from redis.exceptions import RedisError
from sqlalchemy.exc import IntegrityError

from . import db
from .models import User

users_bp = Blueprint("users", __name__, url_prefix="/users")

_CACHE_KEY_ALL_USERS = "users:all"
_CACHE_TTL_SECONDS = 60


def _invalidate_user_cache() -> None:
    try:
        current_app.redis.delete(_CACHE_KEY_ALL_USERS)
    except RedisError:
        pass


@users_bp.route("", methods=["POST"])
def create_user():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    email = data.get("email")

    if not name or not email:
        return jsonify({"error": "Both name and email are required"}), 400

    user = User(name=name, email=email)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email already exists"}), 409

    _invalidate_user_cache()
    return jsonify({"id": user.id, "name": user.name, "email": user.email}), 201


@users_bp.route("", methods=["GET"])
def list_users():
    try:
        cached_users = current_app.redis.get(_CACHE_KEY_ALL_USERS)
    except RedisError:
        cached_users = None

    if cached_users:
        return jsonify(json.loads(cached_users))

    users = User.query.all()
    payload = [{"id": u.id, "name": u.name, "email": u.email} for u in users]

    try:
        current_app.redis.setex(
            _CACHE_KEY_ALL_USERS, _CACHE_TTL_SECONDS, json.dumps(payload)
        )
    except RedisError:
        pass

    return jsonify(payload)


@users_bp.route("/<int:id>", methods=["GET"])
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify({"id": user.id, "name": user.name, "email": user.email})


@users_bp.route("/<int:id>", methods=["PUT"])
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.get_json(silent=True) or {}

    if not data:
        return jsonify({"error": "No fields provided for update"}), 400

    user.name = data.get("name", user.name)
    user.email = data.get("email", user.email)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email already exists"}), 409

    _invalidate_user_cache()
    return jsonify({"id": user.id, "name": user.name, "email": user.email})


@users_bp.route("/<int:id>", methods=["DELETE"])
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    _invalidate_user_cache()
    return "", 204
