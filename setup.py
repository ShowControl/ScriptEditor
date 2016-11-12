try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Script Editor',
    'author': 'bapril',
    'url': 'URL to get it at.',
    'download_url': 'Where to download it.',
    'author_email': 'My email.',
    'version': '0.1',
    'install_requires': ['nose'],
    'packages': ['script_editor'],
    'scripts': [],
    'name': 'script_editor'
}

setup(**config)
