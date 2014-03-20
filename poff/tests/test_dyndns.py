from . import DBTestCase
from poff.models import Domain, DynDNSClient, Record

class DynDNSTest(DBTestCase):

    def set_up(self):
        domain = Domain(name='test.com')
        record = Record(name='www.test.com', type='A', content='127.0.0.1', domain=domain)
        client = DynDNSClient(record=record)
        self.client_key = client.key
        _, self.record_id, self.client_id = self.add_objects(domain, record, client)


    def test_create_client(self):
        response = self.client.post('/records/%d/new-dyndns-client' % self.record_id,
            follow_redirects=True)
        self.assert200(response)
        with self.app.app_context():
            clients = DynDNSClient.query.all()
            self.assertEqual(len(clients), 2)


    def test_update_record(self):
        data = {
            'record': 'www.test.com',
            'key': self.client_key.encode('base64'),
        }
        response = self.client.post('/update-record', data=data, follow_redirects=True)
        self.assert200(response)


    def test_update_record_invalid_key(self):
        data = {
            'record': 'www.test.com',
            'key': 'hopefully invalid',
        }
        response = self.client.post('/update-record', data=data)
        self.assertForbidden(response)


    def test_delete_client(self):
        self.assert200(self.client.delete('/dyndns-clients/%d' % self.client_id, follow_redirects=True))
        with self.app.app_context():
            clients = DynDNSClient.query.all()
            self.assertEqual(len(clients), 0)
