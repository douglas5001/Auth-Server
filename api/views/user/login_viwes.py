from datetime import timedelta
import os

from flask import request
from flask_restful import Resource
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from api import api, jwt
from api.services.user import profile_service
from ...schemas.user import login_schema
from ...services.user import user_service

@jwt.additional_claims_loader
def adicionar_permissoes(identity):
    usuario = user_service.list_user_id(identity)
    permissoes = [p.name for p in usuario.profile.permissions] if usuario.profile else []
    return {
        "permissions": permissoes,
        "is_admin": usuario.is_admin
    }


class LoginResource(Resource):
    def post(self):
        """
        Realizar login e obter tokens de acesso e refresh.
        ---
        tags:
          - Login
        consumes:
          - application/json
        parameters:
          - in: body
            name: body
            required: true
            schema:
              id: LoginRequest
              required:
                - email
                - password
              properties:
                email:
                  type: string
                  example: usuario@email.com
                password:
                  type: string
                  example: senha123
        responses:
          200:
            description: Login realizado com sucesso
            schema:
              id: LoginResponse
              properties:
                access_token:
                  type: string
                refresh_token:
                  type: string
                message:
                  type: string
                  example: login realizado com sucesso
          400:
            description: Erro de validação nos dados de entrada
          401:
            description: Credenciais inválidas
        """
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
        """
        Login com conta Google.
        Recebe o token JWT (ID token) retornado pelo Google Identity Services.

        Exemplo:
        {
          "token": "<ID_TOKEN_DO_GOOGLE>"
        }
        """
        data = request.get_json()
        if not data or "token" not in data:
            return {"error": "Token não informado"}, 400

        token = data["token"]

        try:
            # ✅ Valida o token com o Google
            info = id_token.verify_oauth2_token(
                token, grequests.Request(), 
                os.getenv("GOOGLE_CLIENT_ID")  # guarde no .env
            )

            email = info.get("email")
            name = info.get("name", "Usuário Google")
            picture = info.get("picture")
            google_id = info.get("sub")

            # 🔍 Busca usuário local
            usuario = user_service.list_user_email(email)

            if not usuario:
                # se não existir, cria com perfil padrão
                default_profile = profile_service.list_profile_default()  # cria essa helper se quiser
                usuario = user_service.create_user_google(
                    name=name,
                    email=email,
                    profile_id=default_profile.id if default_profile else None,
                    is_admin=False,
                    image_url=picture
                )

            # 🔑 Gera tokens internos (mesmo esquema do login padrão)
            access_token = create_access_token(identity=usuario.id, expires_delta=timedelta(hours=1))
            refresh_token = create_refresh_token(identity=usuario.id)

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "id": usuario.id,
                    "name": usuario.name,
                    "email": usuario.email,
                    "image": usuario.image
                }
            }, 200

        except ValueError as e:
            return {"error": f"Token inválido: {str(e)}"}, 401
          
api.add_resource(GoogleLoginResource, "/login/google")

api.add_resource(LoginResource, "/login")
# api.add_resource(RefreshTokenResource, "/token/refresh")
