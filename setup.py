"""
Flask-Cache-Stats
--------------
Display cache statistics.
"""
from setuptools import setup


setup(
    name='Flask-Cache-Stats',
    version='0.1.0',
    url='http://github.com/nikhilkalige/flask-cache-stats/',
    license='MIT',
    author='Nikhil Kalige',
    author_email='nikhilkalige@gmail.com',
    description=('Display cache statistics'),
    long_description=__doc__,
    packages=['flask_cache_stats'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask>=0.9',
        'Flask-Cache>=0.13.1',
        'Flask-Login>=0.2.11'
    ],
    test_suite="tests",
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
