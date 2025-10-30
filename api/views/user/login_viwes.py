from datetime import timedelta
import os
from flask import request
from flask_restful import Resource
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token
)
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from api import api, jwt
from api.services.user import user_service, profile_service
from ...schemas.user import login_schema


@jwt.additional_claims_loader
def adicionar_permissoes(identity):
    usuario = user_service.list_user_id(identity)
    permissoes = [p.name for p in usuario.profile.permissions] if usuario.profile else []
    return {"permissions": permissoes, "is_admin": usuario.is_admin}


class LoginResource(Resource):
    def post(self):
        schema = login_schema.LoginSchema()
        erros = schema.validate(request.json)
        if erros:
            return erros, 400

        email = request.json["email"]
        senha = request.json["password"]

        usuario = user_service.list_user_email(email)
        if not (usuario and usuario.show_password(senha)):
            return {"message": "Credenciais inválidas"}, 401

        access_token = create_access_token(identity=usuario.id, expires_delta=timedelta(hours=1))
        refresh_token = create_refresh_token(identity=usuario.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "message": "login realizado com sucesso",
        }, 200


class GoogleLoginResource(Resource):
    def post(self):
        data = request.get_json()
        if not data or "token" not in data:
            return {"error": "Token não informado"}, 400

        token = data["token"]

        try:
            info = id_token.verify_oauth2_token(
                token, grequests.Request(),
                os.getenv("GOOGLE_CLIENT_ID")
            )

            email = info.get("email")
            name = info.get("name", "Usuário Google")
            picture = info.get("picture")
            google_id = info.get("sub")

            usuario = user_service.list_user_google_id(google_id) or user_service.list_user_email(email)

            if not usuario:
                default_profile = profile_service.list_profile_default()
                usuario = user_service.create_user_google(
                    name=name,
                    email=email,
                    google_id=google_id,
                    profile_id=default_profile.id if default_profile else None,
                    is_admin=False,
                    image_url=picture
                )
            else:
                user_service.update_google_id_if_missing(usuario, google_id)

            access_token = create_access_token(identity=usuario.id, expires_delta=timedelta(hours=1))
            refresh_token = create_refresh_token(identity=usuario.id)

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "id": usuario.id,
                    "name": usuario.name,
                    "email": usuario.email,
                    "image": usuario.image,
                    "google_id": usuario.google_id,
                }
            }, 200

        except ValueError as e:
            return {"error": f"Token inválido: {str(e)}"}, 401

api.add_resource(LoginResource, "/login")
api.add_resource(GoogleLoginResource, "/login/google")
