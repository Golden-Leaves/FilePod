import os
import secrets
import tempfile
import zipfile
from datetime import datetime, timezone
from flask import (
    Blueprint, current_app, request, redirect, url_for, flash,
    send_from_directory, send_file, abort
)
from ..forms import UploadFileForm
from ..models import db, File
from ..helpers.mime_categorizer import categorize_file
from ..helpers.general import sanitize_rel_path

bp = Blueprint("transfers_bp", __name__)

@bp.route("/upload/<room_token>/<token>", methods=["POST"])
def upload(room_token, token):
    is_debug = request.args.get("debug", "false").lower() == "true"
    form = UploadFileForm()
    if not form.validate_on_submit():
        flash("Invalid form submission.", "warning")
        return redirect(url_for("room_bp.room", room_token=room_token, token=token))

    files = request.files.getlist("files")
    token = secrets.token_urlsafe(16)

    for f in files:
        if not f:
            flash("No file selected", "warning")
            continue

        rel_path = sanitize_rel_path(f.filename)
        parent_folder = os.path.dirname(rel_path)
        filename = os.path.basename(rel_path)

        storage_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], room_token, token)
        os.makedirs(storage_dir, exist_ok=True)

        stored_path = os.path.join(storage_dir, *rel_path.split("/"))
        os.makedirs(os.path.dirname(stored_path), exist_ok=True)
        f.save(stored_path)

        file_row = File(
            token=token,
            name=filename,
            stored_path=stored_path,
            size=os.path.getsize(stored_path),
            mime=f.mimetype,
            type=categorize_file(file_path=stored_path),
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + current_app.config["DEFAULT_TTL"],
            rel_path=rel_path,
            parent_folder=parent_folder,
            room_token=current_app.config["DEFAULT_ROOM_TOKEN"],
        )
        db.session.add(file_row)

    db.session.commit()

    if is_debug:
        return redirect(url_for("room_bp.room_stable"))
    return redirect(url_for("room_bp.room", room_token=room_token, token="all"))

@bp.route("/download/<room_token>/<token>")
def download(room_token, token):
    current_folder = sanitize_rel_path(request.args.get("current_folder", ""))
    filename = request.args.get("filename")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    tmp.close()

    base_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], room_token, token)
    current_dir = os.path.join(base_dir, current_folder)
    file_path = os.path.join(current_dir, sanitize_rel_path(filename or ""))

    if filename and os.path.isfile(file_path):
        return send_from_directory(
            directory=current_dir,
            path=filename,
            as_attachment=True,
            download_name=filename,
        )

    if os.path.isdir(current_dir):
        with zipfile.ZipFile(tmp.name, "w", zipfile.ZIP_DEFLATED) as archive:
            for root, dirs, files in os.walk(current_dir):
                for file in files:
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, start=current_dir)
                    archive.write(abs_path, arcname=rel_path)
        zip_name = f"{os.path.basename(current_dir)}.zip"
        return send_file(tmp.name, as_attachment=True, download_name=zip_name, mimetype="application/zip")

    abort(404)