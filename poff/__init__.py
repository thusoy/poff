from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from logging import getLogger

_logger = getLogger('poff')

db = SQLAlchemy()

def create_app(config_file=None):
    app = Flask('poff')
    if config_file:
        app.config.from_pyfile(config_file)
    else:
        app.config.from_envvar('POFF_CONFIG_FILE')

    db.init_app(app)

    from . import views

    app.register_blueprint(views.mod)

    @app.teardown_appcontext
    def teardown_appcontext(error):
        """ Commits the session if no error has occured, otherwise rollbacks. """
        if error is None:
            try:
                db.session.commit()
            except Exception: # pylint: disable=broad-except
                # Whoopsie! We can't
                db.session.rollback()
                _logger.exception('Exception happened during teardown commit.')
        else:
            # We have an exception, but it has probably already been handled by the modroriate handlers,
            # so just rollback the session and ignore the error
            db.session.rollback()
        db.session.remove()


    return app
