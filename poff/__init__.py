from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from logging import getLogger

_logger = getLogger('poff')

db = SQLAlchemy()

def create_app(config_file=None):
    _init_logging()

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
                _logger.exception('Exception modened during teardown commit.')
        else:
            # We have an exception, but it has probably already been handled by the modroriate handlers,
            # so just rollback the session and ignore the error
            db.session.rollback()
        db.session.remove()


    return app


def _init_logging():
    import logging
    logging.basicConfig(format='%(asctime)s %(levelname)-10s %(name)s %(message)s', level=logging.DEBUG)


def serve():
    """ CLI entrypoint. Start the server. """
    import argparse
    parser = argparse.ArgumentParser(prog='poff')
    parser.add_argument('-b', '--host',
        metavar='<host>',
        default='127.0.0.1',
        help='Which address to listen to. Default: %(default)s',
    )
    parser.add_argument('-p', '--port',
        metavar='<port>',
        type=int,
        default=5353,
        help='Which port to bind to. Default: %(default)s',
    )
    parser.add_argument('-c', '--config-file',
        metavar='<config-file>',
        help='Config file to use. If none is given, will load from the envvar POFF_CONFIG_FILE.',
    )
    parser.add_argument('-d', '--debug',
        action='store_true',
        default=False,
        help='Show debug inforamtion on errors. DO NOT RUN WITH THIS OPTION IN PRODUCTION!',
    )
    args = parser.parse_args()
    app = create_app(config_file=args.config_file)
    app.run(host=args.host, port=args.port, debug=args.debug)
