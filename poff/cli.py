from  . import create_app, db
from .models import DynDNSClient

import argparse
import logging.config
import yaml
from sqlalchemy.schema import CreateTable


_CONFIG_FILE_PARSER = argparse.ArgumentParser(add_help=False)

_CONFIG_FILE_PARSER.add_argument('-c', '--config-file',
    metavar='<config-file>',
    help='Config file to use. If none is given, will load from the envvar POFF_CONFIG_FILE.',
)


def cli_entry():
    """ CLI entrypoint. """
    parser = argparse.ArgumentParser(prog='poff')

    subparser = parser.add_subparsers(title='action',
        help='Action to be performed',
    )

    add_init_parser(subparser)
    add_serve_parser(subparser)

    args = parser.parse_args()
    args.target(args)


def add_serve_parser(subparser):
    """ Add the parser for the `serve` command. """
    parser = subparser.add_parser('serve',
        help='Run the webserver',
        parents=[_CONFIG_FILE_PARSER],
    )
    parser.add_argument('-H', '--host',
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
    parser.add_argument('-d', '--debug',
        action='store_true',
        default=False,
        help='Show debug inforamtion on errors. DO NOT RUN WITH THIS OPTION IN PRODUCTION!',
    )
    parser.add_argument('-l', '--log-config',
        metavar='<log-config-file>',
        help='Path to a YAML file to load logging config from.',
    )

    parser.set_defaults(target=serve)


def add_init_parser(subparser):
    """ Add the `init` command parser. """
    parser = subparser.add_parser('init',
        help='Create the database tables',
        parents=[_CONFIG_FILE_PARSER],
    )
    parser.add_argument('-p', '--print',
        action='store_true',
        help='Print the table creation SQL instead of executing it. The SQL assumes that the ' +
        'rest of the tables has already been created.',
    )
    parser.set_defaults(target=init)


def serve(args):
    """ Run the webserver. """
    _init_logging(args)
    app = create_app(config_file=args.config_file)
    app.run(host=args.host, port=args.port, debug=args.debug)


def init(args):
    """ Initialize the database tables. """
    app = create_app(config_file=args.config_file)
    with app.app_context():
        if getattr(args, 'print'):
            print(CreateTable(DynDNSClient.__table__).compile(db.engine))
        else:
            db.create_all()


def _init_logging(args):
    if args.log_config:
        with open(args.log_config) as log_config_fh:
            logging_config = yaml.load(log_config_fh)
            logging.config.dictConfig(logging_config)
    else:
        log_format = '%(asctime)s %(levelname)-10s %(name)s %(message)s'
        level = logging.DEBUG if args.debug else logging.INFO
        logging.basicConfig(format=log_format, level=level)
