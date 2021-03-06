from flask_cache import Cache as FlaskCache
from flask_login import login_required
from flask import Blueprint, render_template, jsonify, abort
from flask import request, current_app
from sys import getsizeof
import time
import functools
import logging

logger = logging.getLogger(__name__)


class LogData(object):
    def __init__(self, hot=False, hit=0, miss=0, size=0, access_time=0):
        self.hot = hot
        self.hit = hit
        self.miss = miss
        self.size = size
        self.access_time = access_time

    def __repr__(self):
        return ('hot: {}, hit:{}, miss:{}, size:{}, access_time:{}'
                .format(self.hot, self.hit, self.miss, self.size, self.access_time))

    def data(self):
        return dict(hot=self.hot, hit=self.hit, miss=self.miss,
                    size='{:.3f}'.format(self.size),
                    access_time='{:.5f}'.format(self.access_time))


class Cache(FlaskCache):
    def __init__(self, *args, **kwargs):
        self._log = {}
        super(Cache, self).__init__(*args, **kwargs)

    def __add_log(self, key, hot=False, cold=False, hit=False, miss=False,
                  size=None, access_time=None):
        if key in self._log:
            data = self._log[key]
        else:
            data = LogData()
            self._log[key] = data

        if hot:
            data.hot = True
        elif cold:
            data.hot = False

        if hit:
            data.hit += 1
        if miss:
            data.miss += 1
        if size:
            data.size = size
        if access_time:
            data.access_time = access_time

    def get(self, *args, **kwargs):
        "Proxy function for internal cache object."
        start_time = time.time()
        retval = self.cache.get(*args, **kwargs)
        end_time = (time.time() - start_time) * 1000
        if retval:
            size = getsizeof(retval, 0) / 1024.0
            self.__add_log(args[0], hot=True, hit=True, size=size, access_time=end_time)
        else:
            self.__add_log(args[0], cold=True, miss=True, access_time=end_time)
        return retval

    def set(self, *args, **kwargs):
        "Proxy function for internal cache object."
        retval = self.cache.set(*args, **kwargs)
        print(retval)
        if retval:
            size = getsizeof(args[1], 0) / 1024.0
            self.__add_log(args[0], hot=True, size=size)
        return retval

    def add(self, *args, **kwargs):
        "Proxy function for internal cache object."
        retval = self.cache.add(*args, **kwargs)
        if retval:
            size = getsizeof(args[1], 0) / 1024.0
            self.__add_log(args[0], hot=True, size=size)
        return retval

    def delete(self, *args, **kwargs):
        "Proxy function for internal cache object."
        retval = self.cache.delete(*args, **kwargs)
        if retval:
            self.__add_log(args[0], cold=True)
        return retval

    def get_many(self, *args, **kwargs):
        "Proxy function for internal cache object."
        retval = self.cache.get_many(*args, **kwargs)
        retval = list(retval)
        for idx, key in enumerate(args):
            if retval[idx]:
                size = getsizeof(retval, 0) / 1024.0
                self.__add_log(key, hot=True, hit=True, size=size)
            else:
                self.__add_log(key, cold=True, miss=True)
        return retval

    def delete_many(self, *args, **kwargs):
        retval = self.cache.delete_many(*args, **kwargs)
        if retval:
            for key in args:
                self.__add_log(key, cold=True)
        return retval

    def set_many(self, *args, **kwargs):
        retval = self.cache.set_many(*args, **kwargs)
        if retval:
            for key in args[0]:
                val = args[0][key]
                size = getsizeof(val, 0) / 1024.0
                self.__add_log(key, hot=True, size=size)
        return retval

    def get_log(self):
        data = {}
        for key in self._log:
            data[key] = self._log[key].data()

        return data

    def cached(self, timeout=None, key_prefix='view/%s', unless=None):
        """This is a copy of the flask cache version of cached. This one to one
           copy is not ideal, but a necessasity as the the decorator calls
           self.cache.get() rather than self.get().
        """
        def decorator(f):
            @functools.wraps(f)
            def decorated_function(*args, **kwargs):
                #: Bypass the cache entirely.
                if callable(unless) and unless() is True:
                    return f(*args, **kwargs)

                try:
                    cache_key = decorated_function.make_cache_key(*args, **kwargs)
                    rv = self.get(cache_key)
                except Exception:
                    if current_app.debug:
                        raise
                    logger.exception("Exception possibly due to cache backend.")
                    return f(*args, **kwargs)

                if rv is None:
                    rv = f(*args, **kwargs)
                    try:
                        self.set(cache_key, rv,
                                   timeout=decorated_function.cache_timeout)
                    except Exception:
                        if current_app.debug:
                            raise
                        logger.exception("Exception possibly due to cache backend.")
                        return f(*args, **kwargs)
                return rv

            def make_cache_key(*args, **kwargs):
                if callable(key_prefix):
                    cache_key = key_prefix()
                elif '%s' in key_prefix:
                    cache_key = key_prefix % request.path
                else:
                    cache_key = key_prefix

                return cache_key

            decorated_function.uncached = f
            decorated_function.cache_timeout = timeout
            decorated_function.make_cache_key = make_cache_key

            return decorated_function
        return decorator


class CacheStats(Blueprint):
    def __init__(self, cache_obj, base_template="base.html",
                 enable_clear_api=False, protect_api=True,
                 cache_template="stats_view.html",
                 url_prefix='/cache_stats'):
        self.cache = cache_obj
        self.base_template = base_template
        self.cache_template = cache_template
        self.api_enabled = enable_clear_api

        super(CacheStats, self).__init__("flask_cache_stats", __name__,
                                         template_folder='templates',
                                         static_folder='static',
                                         static_url_path='')
        self.add_url_rule(url_prefix, 'flask_cache_stats', self.stats_view)
        if self.api_enabled:
            url = url_prefix + '/<key>'
            if protect_api:
                api = login_required(self.clear_key)
            else:
                api = self.clear_key

            self.add_url_rule(url, 'flask_cache_clear_key',
                              api, methods=['DELETE'])

    def stats_view(self):
        return render_template(self.cache_template, log=self.cache.get_log(),
                               base_template=self.base_template,
                               api_enabled=self.api_enabled)

    def clear_key(self, key):
        if self.cache.delete(key):
            return jsonify(status='success')
        else:
            abort(404)
