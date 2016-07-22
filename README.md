# Flask-Cache-Stats
[![Build Status](https://img.shields.io/travis/nikhilkalige/flask-cache-stats/master.svg?style=flat-square)](https://travis-ci.org/nikhilkalige/flask-cache-stats)

Flask-Cache-Stats is an extension for flask to display cache statistics and clear keys from the cache using [Flask-Cache](https://github.com/thadeusb/flask-cache) extension.

##Installation
```
pip install flask-cache-stats
```

##Usage
Rather than importing `cache` from `flask_cache` import it from `flask_cache_stats`. It provides the same functionalities as `flask_cache`.

To display the stats you have to use the `CacheStats` blueprint.
```
from flask import Flask
from flask_cache_stats import Cache, CacheStats

app = Flask(__name__)
# Setup cache config
app.config['CACHE_TYPE'] = 'simple'
# Init cache
cache = Cache(app)

# Register cache stats blueprint
stats_blueprint = CacheStats(cache)
app.register_blueprint(stats_blueprint)
```

The cache stats should now be visible at `/cache_stats`.

##Options
`CacheStats` takes a few options
```
def __init__(self, cache_obj, base_template="base.html",
             enable_clear_api=False, protect_api=True,
             cache_template="stats_view.html",
             url_prefix='/cache_stats')

```
- `cache_obj` - Cache object registered with the app.
- `base_template` - The template that should be extended by `cache_template`.
- `cache_template` - The template used to display the stats. The template is provided with the following variables.
    - `log`  - Dictionary cachekey: {hot, cold, hit, miss, size, access_time}.
    - `base_template`: Name of the base template.
    - `api_enabled`: Whether clear api is enabled.
- `enable_clear_api`: Enable api to clear the cache key
- `protect_api`: Whether the clear key api requires login. This will be enabled by default and needs [Flask-Login](https://github.com/maxcountryman/flask-login) to be setup.
- `url_prefix`: The url at which the stats is display.
