import pytest
import os
from flask import Flask
from flask_cache_stats.stats import Cache


@pytest.yield_fixture()
def cache():
    app = Flask(__name__, template_folder=os.path.dirname(__file__))
    app.config['CACHE_TYPE'] = 'simple'

    app.debug = True
    cache = Cache(app)
    yield cache


def test_set(cache):
    cache.set('hi', 'hello')
    assert 'hi' in cache.log

    data = cache.log['hi']
    assert data.hit == 0
    assert data.miss == 0
    assert data.access_time == 0
    assert data.hot is True

    cache.set('hi', 'hello')
    cache.set('tie', 'hello')

    assert 'hi' in cache.log
    assert 'tie' in cache.log


def test_get(cache):
    cache.set('hi', 'hello')
    data = cache.log['hi']
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
    data = cache.log['tie']
    assert data.hot is False
    assert data.hit == 0
    assert data.miss == 1


def test_add(cache):
    cache.add('hi', 'hello')
    data = cache.log['hi']
    assert data.hot is True
    assert data.hit == 0


def test_delete(cache):
    cache.set('hi', 'hello')
    data = cache.log['hi']
    assert data.hot is True

    cache.delete('hi')
    assert data.hot is False

    cache.delete('tie')
    assert 'tie' not in cache.log


def test_hit_miss(cache):
    cache.set('hi', 'hello')
    data = cache.log['hi']
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
        assert key in cache.log
        data = cache.log[key]
        assert data.miss == 1

    cache.set('hi', 'hello')
    cache.get_many(*keys)

    data = cache.log['hi']
    assert data.miss == 1
    assert data.hit == 1
    assert data.hot is True

    data = cache.log['tie']
    assert data.miss == 2
    assert data.hit == 0
    assert data.hot is False


def test_set_many(cache):
    keys = ['hi', 'tie']
    cache_data = {'hi': 'hello', 'tie': 'hello'}
    cache.set_many(cache_data)

    for key in keys:
        assert key in cache.log
        data = cache.log[key]
        assert data.hot is True

    cache.set('hi', 'hello')

    cache.set_many(cache_data)

    for key in keys:
        assert key in cache.log
        data = cache.log[key]
        assert data.hot is True

    assert len(cache.log.keys()) == 2


def test_delete_many(cache):
    keys = ['hi', 'tie']
    cache_data = {'hi': 'hello', 'tie': 'hello'}
    cache.set_many(cache_data)

    cache.delete_many(*keys)
    for key in keys:
        data = cache.log[key]
        assert data.hot is False

    cache.set_many(cache_data)
    cache.delete_many('hi', 'bad')

    data = cache.log['tie']
    assert data.hot is True

    data = cache.log['hi']
    assert data.hot is True

    assert len(cache.log.keys()) == 2
