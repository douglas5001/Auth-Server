from api import ma
from ...models.user import user_model
from marshmallow import fields, post_dump
from flask import url_for

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = user_model.User
        load_instance = True
        fields = ("id", "name", "email", "password", "is_admin", "profile_id", "image")

    name = fields.String(required=True)
    email = fields.String(required=True)
    password = fields.String(required=True)
    profile_id = fields.Integer(required=False)
    is_admin = fields.Boolean(required=True)
    image = fields.String(required=False)

    @post_dump
    def to_absolute_image(self, data, **kwargs):
        img = data.get("image")
        if img:
            data["image"] = url_for("uploads.serve_upload", filename=img, _external=True)
        return data

class UserUpdateSchema(UserSchema):
    password = fields.String(required=False, allow_none=True)