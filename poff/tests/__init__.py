from poff import create_app, db

from functools import partial
import os
import tempfile
import unittest


class DBTestCase(unittest.TestCase):

    # used to create the assertXXX helpers
    _assert_helpers = (
        200,
        400,
        403,
    )

    def _set_up(self):
        self.config_file = tempfile.NamedTemporaryFile(delete=False)
        self.config_file.write('\n'.join([
            'SQLALCHEMY_DATABASE_URI = "sqlite://"',
            'SECRET_KEY = "testkey"',
#            'TESTING = True',
            'WTF_CSRF_ENABLED = False',
        ]).encode('utf-8'))
        self.config_file.close()
        self.app = create_app(self.config_file.name)
        with self.app.app_context():
            db.create_all()
        self.client = self.app.test_client()
        for code in DBTestCase._assert_helpers:
            setattr(self, 'assert%d' % code, partial(self.assert_status_code, code=code))


    def assert_status_code(self, response, code):
        self.assertEqual(response.status_code, code)


    def _tear_down(self):
        os.remove(self.config_file.name)


    def __call__(self, *args, **kwargs):
        self._set_up()
        if hasattr(self, 'set_up'):
            self.set_up()
        super(DBTestCase, self).__call__(*args, **kwargs)
        if hasattr(self, 'tear_down'):
            self.tear_down()
        self._tear_down()


    def add_objects(self, *args):
        ids = []
        with self.app.test_request_context():
            for obj in args:
                db.session.add(obj)
            db.session.commit()
            for obj in args:
                ids.append(obj.id)
        return ids


    def assertForbidden(self, response):
        self.assert403(response)
