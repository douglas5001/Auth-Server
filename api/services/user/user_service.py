import os
import uuid
from ...models.user import user_model
from api import db
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from config import UPLOAD_FOLDER
from flask import current_app

def create_user_google(name, email, profile_id=None, is_admin=False, image_url=None):
    from api.models.user.user_model import User
    user = User(
        name=name,
        email=email,
        password="google-auth",  # placeholder, não será usado
        profile_id=profile_id,
        is_admin=is_admin,
        image=image_url
    )
    db.session.add(user)
    db.session.commit()
    return user

def save_image_file(image_file):
    if not image_file:
        return None

    ext = image_file.filename.rsplit(".", 1)[-1].lower()
    if ext not in current_app.config.get("ALLOWED_EXTENSIONS", set()):
        raise ValueError("Tipo de imagem não permitido. Use PNG, JPG ou JPEG.")

    image_file.seek(0, os.SEEK_END)
    file_size = image_file.tell()
    image_file.seek(0)  # voltar ao início

    if file_size > current_app.config.get("MAX_CONTENT_LENGTH", 2 * 1024 * 1024):
        raise RequestEntityTooLarge("Imagem excede o tamanho máximo permitido de 2MB.")

    filename = secure_filename(image_file.filename)
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(UPLOAD_FOLDER, unique_name)
    image_file.save(path)
    return unique_name

def create_user(user, image_file=None):
    image_name = save_image_file(image_file) if image_file else None
    
    user_bd = user_model.User(name=user.name, email=user.email, password=user.password, profile_id=user.profile_id, is_admin=user.is_admin,  image=image_name)
    user_bd.encrypt_password()
    db.session.add(user_bd)
    db.session.commit()
    return user_bd

def list_user():
    user = user_model.User.query.all()
    return user

def list_user_email(email):
    return user_model.User.query.filter_by(email=email).first()

def list_user_id(id):
    return user_model.User.query.filter_by(id=id).first()

def list_user_email(email):
    return user_model.User.query.filter_by(email=email).first()

def update_user(user_db, new_user, image_file=None):
    user_db.name = new_user.name
    user_db.email = new_user.email
    user_db.profile_id = new_user.profile_id
    user_db.is_admin = new_user.is_admin

    if new_user.password:
        user_db.password = new_user.password
        user_db.encrypt_password()

    if image_file:
        user_db.image = save_image_file(image_file)

    db.session.commit()
    return user_db

def delete_user(user):
    db.session.delete(user)
    db.session.commit()
    