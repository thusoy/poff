from . import DBTestCase
from poff.models import Domain, DynDNSClient, Record

class DynDNSTest(DBTestCase):

    def set_up(self):
        domain = Domain(name='test.com')
        soa_record = Record(name='test.com', type='SOA', content='x y 2014010100', domain=domain)
        record = Record(name='www.test.com', type='A', content='127.0.0.1', domain=domain)
        client = DynDNSClient(record=record)
        self.client_key = client.b64_key
        _, self.soa_id, self.record_id, self.client_id = self.add_objects(domain, soa_record,
            record, client)


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
            'key': self.client_key,
        }
        headers = {
            'X-Forwarded-For': '1.2.3.4',
        }
        response = self.client.post('/update-record', data=data, follow_redirects=True,
            environ_overrides={'REMOTE_ADDR':'127.0.0.1'}, headers=headers,
        )
        self.assert200(response)

        with self.app.app_context():
            # soa serial number should have been updated
            new_serial = Record.query.get(self.soa_id).serial
            self.assertNotEqual(new_serial, '2014010100')

            record = Record.query.get(self.record_id)
            self.assertEqual(record.content, '1.2.3.4')

        response = self.client.post('/update-record', data=data,
            environ_overrides={'REMOTE_ADDR':'127.0.0.1'}, headers=headers)

        # Shouldn't change anything with a second update
        with self.app.app_context():
            self.assertEqual(Record.query.get(self.soa_id).serial, new_serial)


    def test_update_record_invalid_key(self):
        data = {
            'record': 'www.test.com',
            'key': 'hopefully invalid',
        }
        response = self.client.post('/update-record', data=data)
        self.assertForbidden(response)
        with self.app.app_context():
            # soa serial number should NOT have been updated
            self.assertEqual(Record.query.get(self.soa_id).serial, '2014010100')


    def test_delete_client(self):
        self.assert200(self.client.delete('/dyndns-clients/%d' % self.client_id, follow_redirects=True))
        with self.app.app_context():
            clients = DynDNSClient.query.all()
            self.assertEqual(len(clients), 0)
