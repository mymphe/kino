import pytest
from flask import g, session
from kino.db import get_db


def test_register(client, app):
    assert client.get('/auth/register').status_code == 200
    response = client.post(
        '/auth/register', data={'username': 'a', 'email': 'e@ma.il', 'password': 'a'}
    )
    assert 'http://localhost/auth/login' == response.headers['Location']

    with app.app_context():
        assert get_db().execute(
            "SELECT * FROM users WHERE username = 'a'",
        ).fetchone() is not None


@pytest.mark.parametrize(('username', 'email', 'password', 'message'), (
    ('', '', '', b'Username is required.'),
    ('a', '', '', b'Email is required.'),
    ('a', 'e@ma.il', '', b'Password is required.'),
    ('test', 'test@e.mail', 'test', b'already registered')
))
def test_register_validate_input(client, username, email, password, message):
    response = client.post(
        '/auth/register',
        data={'username': username, 'email': email, 'password': password}
    )
    assert message in response.data


def test_login(client, auth):
    assert client.get('/auth/login').status_code == 200
    response = auth.login()
    assert response.headers['Location'] == 'http://localhost/'

    with client:
        client.get('/')
        assert session['user_id'] == 'id-0'
        assert g.user['username'] == 'test'


@pytest.mark.parametrize(('username', 'password', 'message'), (
    ('a', 'test', b'Incorrect username.'),
    ('test', 'a', b'Incorrect password.'),
))
def test_login_validate_input(auth, username, password, message):
    response = auth.login(username, password)
    assert message in response.data


def test_logout(client, auth):
    auth.login()

    with client:
        auth.logout()
        assert 'user_id' not in session
