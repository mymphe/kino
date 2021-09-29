import pytest
from kino.db import get_db


def test_index(client, auth):
    response = client.get('/')
    assert b"Log In" in response.data
    assert b"Register" in response.data

    auth.login()
    response = client.get('/')
    assert b'Log Out' in response.data
    assert b'test title' in response.data
    assert b'by test on 2018-01-01' in response.data
    assert b'test body' in response.data
    assert b'href="/review-id-0/update"' in response.data


@pytest.mark.parametrize('path', (
    '/create',
    '/review-id-0/update',
    '/review-id-0/delete',
))
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers['Location'] == 'http://localhost/auth/login'


def test_author_required(app, client, auth):
    # change the post author to another user
    with app.app_context():
        db = get_db()
        db.execute('UPDATE reviews SET user_id = "id-1" WHERE id = "review-id-0"')
        db.commit()

    auth.login()
    # current user can't modify other user's post
    assert client.post('/review-id-0/update').status_code == 403
    assert client.post('/review-id-0/delete').status_code == 403
    # current user doesn't see edit link
    assert b'href="/review-id-0/update"' not in client.get('/').data


@pytest.mark.parametrize('path', (
    '/review-id-1/update',
    '/review-id-1/delete',
))
def test_exists_required(client, auth, path):
    auth.login()
    assert client.post(path).status_code == 404


def test_create(client, auth, app):
    auth.login()
    assert client.get('/create').status_code == 200
    client.post('/create', data={'title': 'created', 'body': ''})

    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM reviews').fetchone()[0]
        assert count == 2


def test_update(client, auth, app):
    auth.login()
    assert client.get('/review-id-0/update').status_code == 200
    client.post('/review-id-0/update', data={'title': 'updated', 'body': ''})

    with app.app_context():
        db = get_db()
        post = db.execute(
            'SELECT * FROM reviews WHERE id = "review-id-0"').fetchone()
        assert post['title'] == 'updated'


@pytest.mark.parametrize('path', (
    '/create',
    '/review-id-0/update',
))
def test_create_update_validate(client, auth, path):
    auth.login()
    response = client.post(path, data={'title': '', 'body': ''})
    assert b'Title is required.' in response.data


def test_delete(client, auth, app):
    auth.login()
    response = client.post('/review-id-0/delete')
    assert response.headers['Location'] == 'http://localhost/'

    with app.app_context():
        db = get_db()
        post = db.execute(
            'SELECT * FROM reviews WHERE id = "review-id-0"').fetchone()
        assert post is None
