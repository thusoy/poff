from . import DBTestCase
from poff.models import Domain, Record

class RecordTest(DBTestCase):

    def set_up(self):
        domain = Domain(name='test.com')
        soa_record = Record(type='SOA', content='x y 2014010100', name='test.com', domain=domain)
        record = Record(name='www.test.com', type='A', content='127.0.0.1', domain=domain)
        self.domain_id, self.soa_id, self.record_id = self.add_objects(domain, soa_record, record)


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
            self.assertEqual(len(records), 3)

            # soa serial number should have been updated
            self.assertNotEqual(Record.query.get(self.soa_id).serial, '2014010100')


    def test_create_mx_record_default_prio(self):
        data = {
            'name': 'mx.test.com',
            'type': 'MX',
            'content': '127.0.0.1',
        }
        response = self.client.post('/domains/%d/new_record' % self.domain_id, data=data,
            follow_redirects=True)
        self.assert200(response)
        with self.app.app_context():
            records = Record.query.filter_by(type='MX').all()
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].prio, 0)


    def test_invalid_create_record(self):
        data = {
            'name': 'ftp.test.com',
            'type': 'BOGUS',
            'content': 'lols',
        }
        response = self.client.post('/domains/%d/new_record' % self.domain_id, data=data)
        self.assert400(response)


    def test_modify_record(self):
        data = {
            'name': 'www.test.com',
            'type': 'A',
            'content': '127.0.0.2',
        }
        response = self.client.post('/records/%d' % self.record_id, data=data,
            follow_redirects=True)
        self.assert200(response)
        with self.app.app_context():
            record = Record.query.get(self.record_id)
            self.assertEqual(record.content, '127.0.0.2')


    def test_delete_record(self):
        response = self.client.delete('/records/%d' % self.record_id, follow_redirects=True)
        self.assert200(response)
        with self.app.app_context():
            records = Record.query.all()
            self.assertEqual(len(records), 1)

            # soa serial number should have been updated
            self.assertNotEqual(Record.query.get(self.soa_id).serial, '2014010100')


    def test_delete_html(self):
        data = {
            '_method': 'DELETE',
        }
        self.assert200(self.client.post('/records/%d' % self.record_id, data=data,
            follow_redirects=True))


    def test_record_sort_order(self):
        subsubdomains = ['a', 'z', 'b']
        for num, subsubdomain in enumerate(subsubdomains):
            data = {
                'name': '%s.subdomain.test.com' % subsubdomain,
                'type': 'A',
                'content': '127.0.0.%d' % num
            }
            response = self.client.post('/domains/%d/new_record' % self.domain_id, data=data,
                follow_redirects=True)
            self.assert200(response)
        subsubdomains.sort()
        with self.app.app_context():
            domain = Domain.query.get(self.domain_id)
            num = 0
            for record in domain.records:
                if not 'subdomain' in record.name:
                    continue
                self.assertEqual(record.name, subsubdomains[num] + '.subdomain.test.com')
                num += 1
