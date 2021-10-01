import uuid

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from kino.auth import login_required
from kino.db import get_db

bp = Blueprint('user', __name__, url_prefix="/user")


@bp.route('/<username>')
def profile(username):
    db = get_db()
    user = db.execute(
        'SELECT username, title, COUNT(r.id)'
        ' FROM users u'
        ' LEFT JOIN reviews r'
        ' ON u.id = r.user_id'
        ' WHERE username = ?',
        (username,)
    ).fetchone()
    
    if user['username'] is None:
        abort(404, f"User {username} doesn't exist.")


    return render_template('user/profile.html', user=user)
