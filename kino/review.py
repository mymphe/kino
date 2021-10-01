import uuid

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from kino.auth import login_required
from kino.db import get_db

bp = Blueprint('review', __name__)


@bp.route('/')
def index():
    db = get_db()
    reviews = db.execute(
        'SELECT r.id, title, body, created, updated, user_id, username'
        ' FROM reviews r JOIN users u ON r.user_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('review/index.html', reviews=reviews)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO reviews (id, title, body, user_id)'
                ' VALUES (?, ?, ?, ?)',
                (str(uuid.uuid4()), title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('review.index'))

    return render_template('review/create.html')


def get_review(id, check_author=True):
    review = get_db().execute(
        'SELECT r.id, title, body, created, user_id, username'
        ' FROM reviews r JOIN users u ON r.user_id = u.id'
        ' WHERE r.id = ?',
        (id,)
    ).fetchone()

    if review is None:
        abort(404, f"Review id {id} doesn't exist.")

    if check_author and review['user_id'] != g.user['id']:
        abort(403)

    return review


@bp.route('/<id>')
def read(id):
    review = get_review(id, False)
    return render_template('review/read.html', review=review)


@bp.route('/<id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    review = get_review(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE reviews SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('review.index'))

    return render_template('review/update.html', review=review)


@bp.route('/<id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_review(id)
    db = get_db()
    db.execute('DELETE FROM reviews WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('review.index'))
