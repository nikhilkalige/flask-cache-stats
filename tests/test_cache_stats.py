import pytest
import os
from flask import Flask
from flask_cache_stats.stats import Cache, CacheStats
from flask_login import LoginManager, UserMixin, login_user


@pytest.yield_fixture()
def cache():
    app = Flask(__name__, template_folder=os.path.dirname(__file__))
    app.config['CACHE_TYPE'] = 'simple'

    app.debug = True
    cache = Cache(app)
    yield cache


def test_set(cache):
    cache.set('hi', 'hello')
    assert 'hi' in cache._log

    data = cache._log['hi']
    assert data.hit == 0
    assert data.miss == 0
    assert data.access_time == 0
    assert data.hot is True

    cache.set('hi', 'hello')
    cache.set('tie', 'hello')

    assert 'hi' in cache._log
    assert 'tie' in cache._log


def test_get(cache):
    cache.set('hi', 'hello')
    data = cache._log['hi']
    assert data.hot is True
    assert data.hit == 0

    cache.get('hi')
    assert data.hot is True
    assert data.hit == 1
    assert data.miss == 0

    cache.get('hi')
    assert data.hot is True
    assert data.hit == 2
    assert data.miss == 0

    cache.get('tie')
    data = cache._log['tie']
    assert data.hot is False
    assert data.hit == 0
    assert data.miss == 1


def test_add(cache):
    cache.add('hi', 'hello')
    data = cache._log['hi']
    assert data.hot is True
    assert data.hit == 0


def test_delete(cache):
    cache.set('hi', 'hello')
    data = cache._log['hi']
    assert data.hot is True

    cache.delete('hi')
    assert data.hot is False

    cache.delete('tie')
    assert 'tie' not in cache._log


def test_hit_miss(cache):
    cache.set('hi', 'hello')
    data = cache._log['hi']
    assert data.hot is True

    cache.get('hi')
    assert data.hit == 1
    assert data.miss == 0

    cache.delete('hi')
    cache.get('hi')
    assert data.miss == 1
    assert data.hit == 1


def test_get_many(cache):
    keys = ['hi', 'tie']
    cache.get_many(*keys)

    for key in keys:
        assert key in cache._log
        data = cache._log[key]
        assert data.miss == 1

    cache.set('hi', 'hello')
    cache.get_many(*keys)

    data = cache._log['hi']
    assert data.miss == 1
    assert data.hit == 1
    assert data.hot is True

    data = cache._log['tie']
    assert data.miss == 2
    assert data.hit == 0
    assert data.hot is False


def test_set_many(cache):
    keys = ['hi', 'tie']
    cache_data = {'hi': 'hello', 'tie': 'hello'}
    cache.set_many(cache_data)

    for key in keys:
        assert key in cache._log
        data = cache._log[key]
        assert data.hot is True

    cache.set('hi', 'hello')

    cache.set_many(cache_data)

    for key in keys:
        assert key in cache._log
        data = cache._log[key]
        assert data.hot is True

    assert len(cache._log.keys()) == 2


def test_delete_many(cache):
    keys = ['hi', 'tie']
    cache_data = {'hi': 'hello', 'tie': 'hello'}
    cache.set_many(cache_data)

    cache.delete_many(*keys)
    for key in keys:
        data = cache._log[key]
        assert data.hot is False

    cache.set_many(cache_data)
    cache.delete_many('hi', 'bad')

    data = cache._log['tie']
    assert data.hot is True

    data = cache._log['hi']
    assert data.hot is True

    assert len(cache._log.keys()) == 2


class User(UserMixin):
    def __init__(self, name, id, active=True):
        self.id = id
        self.name = name
        self.active = active

    def get_id(self):
        return self.id

    @property
    def is_active(self):
        return self.active


valid = User(u'valid', 1)
invalid = User(u'invalid', 2, False)

USERS = [valid, invalid]


@pytest.yield_fixture()
def app_login():
    app = Flask(__name__)
    app.debug = True
    app.config['SECRET_KEY'] = 'deterministic'
    app.config['SESSION_PROTECTION'] = None
    app.config['REMEMBER_COOKIE_NAME'] = 'remember'
    app.config['CACHE_TYPE'] = 'simple'

    cache = Cache(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager._login_disabled = False

    @login_manager.user_loader
    def load_user(user_id):
        return USERS[int(user_id)]

    yield app, cache


def test_api_unprotected(app_login):
    app, cache = app_login
    stats_bp = CacheStats(cache, enable_clear_api=True, protect_api=False)
    app.register_blueprint(stats_bp)
    cache.set('hi', 'hello')

    with app.test_client() as c:
        result = c.delete('cache_stats/asdf')
        assert result.status_code == 404

        result = c.delete('cache_stats/hi')
        assert result.status_code == 200


def test_api_prefix(app_login):
    app, cache = app_login
    stats_bp = CacheStats(cache, url_prefix="/test", enable_clear_api=True,
                          protect_api=False)
    app.register_blueprint(stats_bp)
    cache.set('hi', 'hello')

    with app.test_client() as c:
        result = c.delete('test/hi')
        assert result.status_code == 200


def test_api_protected(app_login):
    app, cache = app_login
    stats_bp = CacheStats(cache, enable_clear_api=True,
                          protect_api=True)
    app.register_blueprint(stats_bp)

    @app.route('/login-valid')
    def login_valid():
        return str(login_user(valid))

    @app.route('/login-invalid')
    def login_invalid():
        return str(login_user(invalid))

    with app.test_request_context():
        with app.test_client() as c:
            c.get('/login-valid')
            cache.set('hi', 'hello')
            result = c.delete('cache_stats/hi')
            assert result.status_code == 200

    with app.test_request_context():
        with app.test_client() as c:
            cache.set('hi', 'hello')
            result = c.delete('cache_stats/hi')
            assert result.status_code == 401

            c.get('login-invalid')
            result = c.delete('cache_stats/hi')
            assert result.status_code == 401
