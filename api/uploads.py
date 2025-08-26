from flask import Blueprint, send_from_directory
from config import UPLOAD_FOLDER

uploads_bp = Blueprint("uploads", __name__)

@uploads_bp.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)
