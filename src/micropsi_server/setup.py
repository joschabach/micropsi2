from os.path import abspath, dirname, join
from setuptools import setup, find_packages

version = '0.1'

here = abspath(dirname(__file__))
README = open(join(here, 'README.txt')).read()
CHANGES = open(join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid',
    'WebError',
    'kotti'
]

setup(name='micropsi_server',
    version=version,
    description='MicroPsi2, Webserver edition',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    tests_require=requires,
    test_suite="micropsi_server",
    entry_points="""
        [paste.app_factory]
        main = micropsi_server:main
    """,
    paster_plugins=['pyramid'],
)
