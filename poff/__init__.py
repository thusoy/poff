from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from logging import getLogger
import textwrap

_logger = getLogger('poff')

db = SQLAlchemy()

def create_app(config_file=None):
    app = Flask('poff')
    if config_file:
        app.config.from_pyfile(config_file)
    else:
        app.config.from_envvar('POFF_CONFIG_FILE')

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

    @app.errorhandler(500)
    def server_error(error):
        generic_error_handler(error)
        # Don't rely on any special mechanisms such as template loading or other resources,
        # as we don't know where the error is.
        return textwrap.dedent('''\
        <!doctype html>
        <title>Internal Server Error</title>
        <h1>Internal Server Error</h1>
        <p>
            I'm very sorry to report this, but something has gone wrong on the server.
            If you have administrator access, check the logs for more details, otherwise
            you should probably gently notify your sysadmin of the failure.
        ''')


    return app

def generic_error_handler(exception):
    """ Log exception to the standard logger. """
    log_msg = textwrap.dedent("""Error occured.
        Path:                 %s
        Params:               %s
        HTTP Method:          %s
        Client IP Address:    %s
        User Agent:           %s
        User Platform:        %s
        User Browser:         %s
        User Browser Version: %s
        HTTP Headers:         %s
        Exception:            %s
        """ % (
            request.path,
            request.values,
            request.method,
            request.remote_addr,
            request.user_agent.string,
            request.user_agent.platform,
            request.user_agent.browser,
            request.user_agent.version,
            request.headers,
            exception
        )
    )
    _logger.exception(log_msg)
