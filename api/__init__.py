import os
from flask import Flask
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager
from flasgger import Swagger
import pymysql
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)
ma = Marshmallow(app)
migrate = Migrate(app, db)
api = Api(app)
jwt = JWTManager(app)


# CORS(app, origins=[
#     "http://localhost:3000",
#     "http://147.93.183.190:3000",
#     "https://hubble.muppet.com.br"
# ], supports_credentials=True)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)


swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "API REST FULL",
        "description": "Documentação da API com autenticação JWT",
        "version": "1.0.0"
    },
    "securityDefinitions": {
        "BearerAuth": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header usando o esquema Bearer. Exemplo: 'Bearer {seu_token}'"
        }
    }
}

swagger = Swagger(app, template=swagger_template)


from config import UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

from api.uploads import uploads_bp
app.register_blueprint(uploads_bp)

from .views.user import user_views, login_viwes, permission_views, profile_views, refresh_toke_views

from .models.user import profile_permission_model, user_model
