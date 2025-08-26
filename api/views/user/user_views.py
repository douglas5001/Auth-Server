from flask_restful import Resource
from api import api
from api.services.user import profile_service
from ...permission_required import permission_required
from ...schemas.user import user_schema
from flask import request, make_response, jsonify
from ...entity.user import user
from ...services.user import user_service
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import RequestEntityTooLarge


class userList(Resource):
    @permission_required("listuser")
    def get(self):
        """
        Lista todos os usuários cadastrados.

        ⚠️ **Requer token JWT no header**  
        Exemplo de header:
        Authorization: Bearer **<seu_token_aqui>**

        ---
        tags:
          - User
        security:
          - BearerAuth: []
        responses:
          200:
            description: Lista de usuários retornada com sucesso
            schema:
              type: array
              items:
                properties:
                  id:
                    type: integer
                  name:
                    type: string
                  email:
                    type: string
                  profile_id:
                    type: integer
                  is_admin:
                    type: boolean
          401:
            description: Token ausente ou inválido
        """
        users = user_service.list_user()
        us = user_schema.UserSchema(many=True)
        return make_response(us.jsonify(users))

    def post(self):
        """
        Criar um novo usuário e vinculá-lo a um perfil existente, com opção de enviar imagem de perfil.

        ---
        tags:
          - User
        consumes:
          - multipart/form-data
        parameters:
          - in: formData
            name: name
            type: string
            required: true
            description: Nome do usuário
          - in: formData
            name: email
            type: string
            required: true
            description: E-mail do usuário
          - in: formData
            name: password
            type: string
            required: true
            description: Senha do usuário
          - in: formData
            name: profile_id
            type: integer
            required: true
            description: ID do perfil associado
          - in: formData
            name: is_admin
            type: boolean
            required: true
            description: Define se o usuário é administrador
          - in: formData
            name: image
            type: file
            required: false
            description: Imagem de perfil do usuário
        responses:
          201:
            description: Usuário criado com sucesso
          400:
            description: E-mail já cadastrado ou dados inválidos
        """
        form = request.form

        us = user_schema.UserSchema()
        validate = us.validate(form)
        if validate:
            return make_response(jsonify(validate), 400)

        name = form["name"]
        email = form["email"]
        password = form["password"]
        profile_id = int(form["profile_id"])
        is_admin = form["is_admin"].lower() == 'true'
        file = request.files.get("image")

        list_profile = profile_service.list_profile_id(profile_id)
        if list_profile is None:
            return make_response(jsonify("perfil não existe"), 400)
          
        existing_user = user_service.list_user_email(email)
        if existing_user:
            return make_response(jsonify({"error": "E-mail já está em uso"}), 400)

        new_user = user.User(
            name=name,
            email=email,
            password=password,
            profile_id=profile_id,
            is_admin=is_admin
        )

        try:
            resultado = user_service.create_user(new_user, image_file=file)
        except ValueError as ve:
            return make_response(jsonify({"error": str(ve)}), 400)
        except RequestEntityTooLarge as re:
            return make_response(jsonify({"error": str(re)}), 413)
          
          
        return make_response(us.jsonify(resultado), 201)
      
class userDetail(Resource):
  def get(self, id):
    """
    Buscar um usuário específico pelo ID.

    ⚠️ **Requer token JWT no header**  
    Exemplo de header:
    Authorization: Bearer **<seu_token_aqui>**

    ---
    tags:
      - User
    parameters:
      - in: path
        name: id
        type: integer
        required: true
        description: ID do usuário a ser buscado
    security:
      - BearerAuth: []
    responses:
      200:
        description: Usuário encontrado com sucesso
        schema:
          properties:
            id:
              type: integer
            name:
              type: string
            email:
              type: string
            profile_id:
              type: integer
            is_admin:
              type: boolean
            image:
              type: string
      404:
        description: Usuário não encontrado
      401:
        description: Token ausente ou inválido
    """
    user = user_service.list_user_id(id)
    if user is None:
      return make_response(jsonify("Usuario não encontrado"), 404)
    schema = user_schema.UserSchema()
    return make_response(schema.jsonify(user))
  
  def put(self, id):
    user_db = user_service.list_user_id(id)
    if user_db is None:
        return make_response(jsonify("Usuário não encontrado"), 404)

    schema = user_schema.UserUpdateSchema()
    validate = schema.validate(request.form)
    if validate:
        return make_response(jsonify(validate), 400)

    name = request.form["name"]
    email = request.form["email"]
    password = request.form.get("password")  # pode vir vazio ou não vir
    profile_id = int(request.form["profile_id"])
    is_admin = request.form["is_admin"].lower() == "true"
    file = request.files.get("image")

    profile = profile_service.list_profile_id(profile_id)
    if profile is None:
        return make_response(jsonify("Perfil não encontrado"), 404)

    new_user = user.User(
        name=name,
        email=email,
        password=password or None,
        profile_id=profile_id,
        is_admin=is_admin,
    )

    try:
        updated_user = user_service.update_user(user_db, new_user, image_file=file)
    except ValueError as ve:
        return make_response(jsonify({"error": str(ve)}), 400)
    except RequestEntityTooLarge as re:
        return make_response(jsonify({"error": str(re)}), 413)

    return make_response(schema.jsonify(updated_user), 200)



api.add_resource(userList, '/users')
api.add_resource(userDetail, '/users/<int:id>')
