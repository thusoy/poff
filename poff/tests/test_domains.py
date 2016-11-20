from . import DBTestCase
from poff.models import Domain, Record, DomainMeta, TsigKey

import datetime
import re

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
            domains = Domain.query.filter(Domain.id != self.domain_id).all()
            self.assertEqual(len(domains), 1)

            # SOA record should have been created
            soa_record = Record.query.filter(Record.type=='SOA', Record.name=='test.com').one()
            today = datetime.datetime.now()
            self.assertEqual(soa_record.serial, today.strftime('%Y%m%d00'))

            # No-mail SPF record should have been created
            spf_record = Record.query.filter(Record.type=='TXT',
                Record.name=='test.com').one()
            self.assertEqual(spf_record.content, 'v=spf1 -all')

            # SOA-EDIT should be set
            soa_edit_record = DomainMeta.query.filter_by(domain=domains[0], kind='SOA-EDIT').first()
            self.assertEqual(soa_edit_record.content, 'INCEPTION-INCREMENT')

            # Should add NSEC3 parameters
            nsec3params = DomainMeta.query.filter_by(domain=domains[0], kind='NSEC3PARAMS').first()
            self.assertTrue(re.match(r'^1 0 1 [a-f0-9]{32}$', nsec3params.content))

            # Should set NSEC3 to narrow mode
            nsec3narrow = DomainMeta.query.filter_by(domain=domains[0], kind='NSEC3NARROW').first()
            self.assertEqual(nsec3narrow.content, '1')


    def test_create_tsigkey(self):
        data = {
            'name': 'testkey',
        }
        response = self.client.post('/domains/%d/tsigkeys' % self.domain_id, data=data,
            follow_redirects=True)
        self.assert200(response)

        with self.app.app_context():
            tsigkeys = TsigKey.query.all()
            self.assertEqual(len(tsigkeys), 1)

            domain_tsigkeys = DomainMeta.query\
                .filter_by(domain_id=self.domain_id, kind='TSIG-ALLOW-DNSUPDATE').all()
            self.assertEqual(len(domain_tsigkeys), 1)
            self.assertEqual(domain_tsigkeys[0].content, 'testkey')


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
