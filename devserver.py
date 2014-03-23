from poff import create_app, db

from os import path


dev_config = path.abspath(path.join(path.dirname(__file__), 'dev_config.py'))

app = create_app(dev_config)

with app.app_context():
    db.create_all()

app.run(debug=True, port=5353)
