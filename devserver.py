#!./venv/bin/python

import logging
from os import path

from poff import create_app, db

log_format = '%(asctime)s %(levelname)-10s %(name)s %(message)s'
logging.basicConfig(format=log_format, level=logging.DEBUG)

dev_config = path.abspath(path.join(path.dirname(__file__), 'dev_config.py'))

app = create_app(dev_config)

with app.app_context():
    db.create_all()

app.run(debug=True, port=5353)
