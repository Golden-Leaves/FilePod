import os
from datetime import datetime, timezone
from flask import Blueprint, current_app, render_template, request, jsonify
from ..forms import UploadFileForm
from ..models import db, File
from ..helpers.general import get_children, get_breadcrumbs, cleanup_expired_tokens

bp = Blueprint("room_bp", __name__)

@bp.route("/room/<room_token>/<token>", methods=["GET", "POST"])
def room(room_token, token):
    room_token = current_app.config["DEFAULT_ROOM_TOKEN"]
    current_folder = request.args.get("current_folder", "")

    cleanup_expired_tokens(current_app.config["UPLOAD_FOLDER"], room_token=room_token)

    breadcrumbs = get_breadcrumbs(current_folder=current_folder)
    form = UploadFileForm()

    subfolders, files, rel_paths = get_children(
        token=token,
        room_token=room_token,
        current_folder=current_folder,
    )

    return render_template(
        "room.html",
        form=form,
        subfolders=subfolders,
        files=files,
        room_token=room_token,
        token=token,
        breadcrumbs=breadcrumbs,
    )

@bp.route("/room-stable")
def room_stable():
    form = UploadFileForm()
    now = datetime.now(timezone.utc)
    uploaded_files = db.session.execute(
        db.select(File).where(File.expires_at > now)
    ).scalars().all()
    return render_template(
        "room-stable.html",
        form=form,
        uploaded_files=uploaded_files,
        room_token=current_app.config["DEFAULT_ROOM_TOKEN"],
    )

@bp.route("/test")
def test():
    current_folder = request.args.get("current_folder", "")
    token = request.args.get("token", "all")
    subfolders, files, rel_paths = get_children(
        token=token,
        current_folder=current_folder,
        room_token=current_app.config["DEFAULT_ROOM_TOKEN"],
    )
    return jsonify({
        "subfolders": [
            {"name": sf["name"], "token": sf["token"], "path": sf["path"]}
            for sf in subfolders
        ],
        "files": [file.name for file in files],
        "rel_paths": rel_paths,
    })