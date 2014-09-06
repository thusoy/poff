from . import DBTestCase
from poff.models import Domain, Record

import datetime

class DomainTest(DBTestCase):

    def set_up(self):
        domain = Domain(name='example.com')
        record = Record(name='www.example.com', type='A', content='127.0.0.1', domain=domain)
        self.domain_id, _ = self.add_objects(domain, record)


    def test_create_domain(self):
        data = {
            'name': 'test.com',
        }
        response = self.client.post('/domains', data=data, follow_redirects=True)
        self.assert200(response)
        with self.app.app_context():
            domains = Domain.query.all()
            self.assertEqual(len(domains), 2)

            # SOA record should have been created
            soa_record = Record.query.filter(Record.type=='SOA', Record.name=='test.com').one()
            today = datetime.datetime.now()
            self.assertEqual(soa_record.serial, today.strftime('%Y%m%d00'))


    def test_create_invalid_domain(self):
        data = {
            'name': '',
        }
        response = self.client.post('/domains', data=data, follow_redirects=True)
        self.assert400(response)


    def test_delete_domain(self):
        response = self.client.delete('/domains/%d' % self.domain_id, follow_redirects=True)
        self.assert200(response)
        with self.app.app_context():
            domains = Domain.query.all()
            self.assertEqual(len(domains), 0)

            # associated records should have been cascade deleted
            records = Record.query.all()
            self.assertEqual(len(records), 0)


    def test_update_soa_serial(self):
        soa_record = Record(type='SOA', content='x y 2014010100')
        new_date = datetime.date(2014, 1, 2)
        soa_record.update_serial(new_date)
        self.assertEqual(soa_record.serial, '2014010200')
        soa_record.update_serial(new_date)
        self.assertEqual(soa_record.serial, '2014010201')
        soa_record.update_serial()
        today = datetime.datetime.now()
        self.assertEqual(soa_record.serial, today.strftime('%Y%m%d00'))
