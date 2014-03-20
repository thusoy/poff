from . import DBTestCase
from poff.models import Domain, Record

class RecordTest(DBTestCase):

    def set_up(self):
        domain = Domain(name='test.com')
        record = Record(name='www.test.com', type='A', content='127.0.0.1', domain=domain)
        self.domain_id, self.record_id = self.add_objects(domain, record)


    def test_create_record(self):
        data = {
            'name': 'ftp.test.com',
            'type': 'A',
            'content': '127.0.0.1',
        }
        response = self.client.post('/domains/%d/new_record' % self.domain_id, data=data,
            follow_redirects=True)
        self.assert200(response)
        with self.app.app_context():
            records = Record.query.all()
            self.assertEqual(len(records), 2)


    def test_delete_record(self):
        response = self.client.delete('/records/%d' % self.record_id, follow_redirects=True)
        self.assert200(response)
        with self.app.app_context():
            records = Record.query.all()
            self.assertEqual(len(records), 0)


    def test_delete_html(self):
        data = {
            '_method': 'DELETE',
        }
        self.assert200(self.client.post('/records/%d' % self.record_id, data=data,
            follow_redirects=True))
