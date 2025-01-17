# services/users/project/api/users/views.py


from functools import wraps

from flask import request, jsonify, current_app
from flask_restplus import Resource, fields, Namespace

import jwt

from project.api.users.services import (
    get_all_users,
    get_user_by_email,
    add_user,
    get_user_by_id,
    update_user,
    delete_user,
)

from project.api.users.models import User


users_namespace = Namespace("users")

user = users_namespace.model(
    "User",
    {
        "id": fields.Integer(readOnly=True),
        "username": fields.String(required=True),
        "email": fields.String(required=True),
        "created_date": fields.DateTime,
    },
)

user_post = users_namespace.inherit(
    "User post", user, {"password": fields.String(required=True)}
)


def jwt_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):

        token = None

        if 'Authorization' in request.headers:
            auth_header = request.headers.get("Authorization")
            token = auth_header
            resp = User.decode_token(token)

        if not resp:
            users_namespace.abort(404, f"a valid token is missing")

        try:
            user = get_user_by_id(resp)
            if not user:
                users_namespace.abort(404, f"User does not exist")
        except Exception as e:
            users_namespace.abort(404, f"a valid token is missing")

        return f(*args, **kwargs)
    return decorator


class UsersList(Resource):
    @jwt_required
    @users_namespace.marshal_with(user, as_list=True)
    def get(self):
        """Returns all users."""
        return get_all_users(), 200

    @jwt_required
    @users_namespace.expect(user_post, validate=True)
    @users_namespace.response(201, "<user_email> was added!")
    @users_namespace.response(400, "Sorry. That email already exists.")
    def post(self):
        """Creates a new user."""
        post_data = request.get_json()
        username = post_data.get("username")
        email = post_data.get("email")
        password = post_data.get("password")
        response_object = {}

        user = get_user_by_email(email)
        if user:
            response_object["message"] = "Sorry. That email already exists."
            return response_object, 400
        add_user(username, email, password)
        response_object["message"] = f"{email} was added!"
        return response_object, 201


class Users(Resource):
    @jwt_required
    @users_namespace.marshal_with(user)
    @users_namespace.response(200, "Success")
    @users_namespace.response(404, "User <user_id> does not exist")
    def get(self, user_id):
        """Returns a single user."""
        user = get_user_by_id(user_id)
        if not user:
            users_namespace.abort(404, f"User {user_id} does not exist")
        return user, 200

    @jwt_required
    @users_namespace.expect(user, validate=True)
    @users_namespace.response(200, "<user_is> was updated!")
    @users_namespace.response(404, "User <user_id> does not exist")
    def put(self, user_id):
        """Updates a user."""
        post_data = request.get_json()
        username = post_data.get("username")
        email = post_data.get("email")
        response_object = {}

        user = get_user_by_id(user_id)
        if not user:
            users_namespace.abort(404, f"User {user_id} does not exist")
        update_user(user, username, email)
        response_object["message"] = f"{user.id} was updated!"
        return response_object, 200

    @jwt_required
    @users_namespace.response(200, "<user_is> was removed!")
    @users_namespace.response(404, "User <user_id> does not exist")
    def delete(self, user_id):
        """Updates a user."""
        response_object = {}
        user = get_user_by_id(user_id)
        if not user:
            users_namespace.abort(404, f"User {user_id} does not exist")
        delete_user(user)
        response_object["message"] = f"{user.email} was removed!"
        return response_object, 200


users_namespace.add_resource(UsersList, "")
users_namespace.add_resource(Users, "/<int:user_id>")
