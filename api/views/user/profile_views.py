from flask import jsonify, make_response, request
from flask_restful import Resource

from api import api
from ...schemas.user import profile_permission_schema
from ...services.user import profile_permission_service
from ...permission_required import permission_required
from ...entity.user import profile_permission

class ProfileList(Resource):
    # @permission_required("profile:create")
    def get(self):
      """
      Listar todos os perfis cadastrados.

      ---
      tags:
        - Profile
      responses:
        200:
          description: Lista de perfis obtida com sucesso
          schema:
            type: array
            items:
              $ref: '#/definitions/ProfileResponse'
      """
      profile = profile_permission_service.list_profile()
      schema = profile_permission_schema.ProfileSchema(many=True)
      return make_response(schema.jsonify(profile))
    
    def post(self):
        """
        Criar um novo perfil e vincular permissões existentes.

        Exemplo de JSON no corpo da requisição:
        {
          "name": "Administrador",
          "permission_ids": [1, 2, 3]
        }
        ---
        tags:
          - Profile
        consumes:
          - application/json
        parameters:
          - in: body
            name: body
            required: true
            schema:
              id: ProfileRequest
              required:
                - name
              properties:
                name:
                  type: string
                  example: Administrador
                permission_ids:
                  type: array
                  items:
                    type: integer
                  example: [1, 2, 3]
        responses:
          201:
            description: Perfil criado com sucesso
            schema:
              id: ProfileResponse
              properties:
                id:
                  type: integer
                name:
                  type: string
                permissions:
                  type: array
                  items:
                    type: string
          400:
            description: Erro de validação nos dados de entrada
        """
        schema = profile_permission_schema.ProfileSchema()
        errors = schema.validate(request.json)

        if errors:
            return make_response(jsonify(errors), 400)

        data = request.json
        name = data["name"]
        permission_ids = data.get("permission_ids", [])

        profile = profile_permission.Profile(name=name, permission_ids=permission_ids)
        result = profile_permission_service.create_profile(profile)

        return make_response(schema.jsonify(result), 201)

api.add_resource(ProfileList, "/profiles")


class ProfileDetail(Resource):
  def delete(self, id):
    """
    Excluir um perfil existente pelo ID.

    ---
    tags:
      - Profile
    parameters:
      - in: path
        name: id
        required: true
        type: integer
        description: ID do perfil a ser excluído
    responses:
      204:
        description: Perfil excluído com sucesso (sem conteúdo)
      404:
        description: Perfil não encontrado
    """
    profile = profile_permission_service.list_profile_id(id)
    if profile is None:
      return make_response(jsonify("Profile não encontrado"), 404)
    profile_permission_service.delete_profile(profile)

    return make_response("Profile Excluido", 204)
  
  def put(self, id):
    """
    Atualizar um perfil existente pelo ID.

    ---
    tags:
      - Profile
    parameters:
      - in: path
        name: id
        required: true
        type: integer
        description: ID do perfil a ser atualizado
      - in: body
        name: body
        required: true
        schema:
          id: ProfileUpdate
          required:
            - name
          properties:
            name:
              type: string
              example: Coordenador
            permission_ids:
              type: array
              items:
                type: integer
              example: [1, 2, 3]
    responses:
      200:
        description: Perfil atualizado com sucesso
        schema:
          id: ProfileResponse
          properties:
            id:
              type: integer
              example: 2
            name:
              type: string
              example: Coordenador
            permissions:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  name:
                    type: string
                    example: permission:create
      400:
        description: Erro de validação nos dados de entrada
      404:
        description: Perfil não encontrado
    """
    profile = profile_permission_service.list_profile_id(id)
    if profile is None:
      return make_response(jsonify("Perfil não existe"), 404)
    
    schema = profile_permission_schema.ProfileSchema()
    validate = schema.validate(request.json)
    if validate:
      return make_response(jsonify(validate), 400)
    else:
        data = request.json
        name = data["name"]
        permission_ids = data.get("permission_ids", [])

        new_profile = profile_permission.Profile(name=name, permission_ids=permission_ids)

        profile_permission_service.put_profile(profile, new_profile)
        
        update_profile = profile_permission_service.list_profile_id(id)
        
        return make_response(schema.jsonify(update_profile), 200)



api.add_resource(ProfileDetail, "/profiles/<int:id>")

class ProfilePermissionAttach(Resource):
    def post(self, profile_id):
        """
        Adicionar permissões a um perfil existente.

        Envie um array de IDs de permissões para vincular ao perfil.

        ---
        tags:
          - Profile
        consumes:
          - application/json
        parameters:
          - in: path
            name: profile_id
            required: true
            description: ID do perfil que receberá as permissões
            type: integer
          - in: body
            name: body
            required: true
            schema:
              id: AttachPermissionsRequest
              required:
                - permission_ids
              properties:
                permission_ids:
                  type: array
                  items:
                    type: integer
                  example: [1, 2, 3]
        responses:
          200:
            description: Permissões adicionadas com sucesso ao perfil
            schema:
              id: AttachPermissionsResponse
              properties:
                id:
                  type: integer
                  example: 1
                name:
                  type: string
                  example: Administrador
                permissions:
                  type: array
                  items:
                    type: object
                    properties:
                      id:
                        type: integer
                        example: 2
                      name:
                        type: string
                        example: permission:create
          400:
            description: Erro de validação nos dados de entrada
            schema:
              properties:
                error:
                  type: string
                  example: permission_ids deve ser uma lista
          404:
            description: Perfil não encontrado
            schema:
              properties:
                error:
                  type: string
                  example: Perfil não encontrado
        """
        data = request.json
        if "permission_ids" not in data or not isinstance(data["permission_ids"], list):
            return make_response(jsonify({"error": "permission_ids deve ser uma lista"}), 400)

        permission_ids = data["permission_ids"]
        profile = profile_permission_service.add_permissions_to_profile(profile_id, permission_ids)

        if not profile:
            return make_response(jsonify({"error": "Perfil não encontrado"}), 404)

        schema = profile_permission_schema.ProfileSchema()
        return make_response(schema.jsonify(profile), 200)


api.add_resource(ProfilePermissionAttach, "/profiles/<int:profile_id>/permissions")