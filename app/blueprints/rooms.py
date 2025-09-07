from flask import Blueprint, render_template

bp = Blueprint("rooms_bp", __name__)

@bp.route("/rooms")
def rooms():
    return render_template("rooms.html")