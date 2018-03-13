from . import DBTestCase
from poff.models import Domain, Record, DomainMeta, TsigKey

import datetime
import re

class DomainTest(DBTestCase):

    def set_up(self):
        domain = Domain(name='example.com')
        soa_record = Record(name='example.com', type='SOA', content='example.com hostmaster.example.com 1970010101', domain=domain)
        record = Record(name='www.example.com', type='A', content='127.0.0.1', domain=domain)
        self.domain_id, _, _ = self.add_objects(domain, record, soa_record)


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


    def test_mname_validation(self):
        invalid_mnames = (
            'with spaces.example.com',
        )
        for invalid_mname in invalid_mnames:
            self.assert400(self.client.post('/domains', data={
                'name': 'example.com',
                'mname': invalid_mname,
            }))

        valid_mnames = (
            'example.com',
            'ns.example.com',
            'otherdomain.tld',
        )
        for valid_mname in valid_mnames:
            self.assert200(self.client.post('/domains', data={
                'name': 'example.com',
                'mname': valid_mname,
            }, follow_redirects=True))


    def test_rname_validation(self):
        invalid_rnames = (
            'with spaces@example.com',
            'notld',
        )
        for invalid_rname in invalid_rnames:
            self.assert400(self.client.post('/domains', data={
                'name': 'example.com',
                'rname': invalid_rname,
            }))

        valid_rnames = (
            'me@exammple.com',
            'me.example.com',
            'some.gal123@gmail.co.uk',
        )
        for valid_rname in valid_rnames:
            self.assert200(self.client.post('/domains', data={
                'name': 'example.com',
                'rname': valid_rname,
            }, follow_redirects=True))


    def test_modify_mname(self):
        response = self.client.post('/domains/%d' % self.domain_id, data={
            'mname': 'ns.example.com',
            'rname': 'john.doe@example.com',
        }, follow_redirects=True)
        self.assert200(response)

        with self.app.app_context():
            soa_record = Record.query.filter(Record.type=='SOA').one()
            mname, rname, serial = soa_record.content.split(' ')[:3]
            self.assertEqual(mname, 'ns.example.com')
            self.assertEqual(rname, 'john\.doe.example.com')
            self.assertNotEqual(serial, '1970010101')


    def test_modify_mname_invalid(self):
        self.assert400(self.client.post('/domains/%d' % self.domain_id, data={
            'mname': 'ns with spaces.com',
        }))


    def test_modify_rname_invalid(self):
        self.assert400(self.client.post('/domains/%d' % self.domain_id, data={
            'rname': 'with spaces@gmail.com',
        }))


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


    def test_delete_tsigkey(self):
        tsigkey = TsigKey(name='testkey')
        tsigmeta = DomainMeta(domain_id=self.domain_id, kind='TSIG-ALLOW-DNSUPDATE',
            content='testkey')
        self.add_objects(tsigkey, tsigmeta)

        response = self.client.delete('/domains/%d/tsigkeys/testkey' % self.domain_id,
            follow_redirects=True)

        self.assert200(response)
        with self.app.app_context():
            self.assertEqual(len(TsigKey.query.all()), 0)
            self.assertEqual(len(DomainMeta.query.all()), 0)


    def test_delete_tsigkey_over_post(self):
        tsigkey = TsigKey(name='testkey')
        tsigmeta = DomainMeta(domain_id=self.domain_id, kind='TSIG-ALLOW-DNSUPDATE',
            content='testkey')
        self.add_objects(tsigkey, tsigmeta)

        response = self.client.post('/domains/%d/tsigkeys/testkey' % self.domain_id,
            data={'_method': 'DELETE'}, follow_redirects=True)

        self.assert200(response)
        with self.app.app_context():
            self.assertEqual(len(TsigKey.query.all()), 0)
            self.assertEqual(len(DomainMeta.query.all()), 0)


    def test_delete_nonexisting_tsigkey(self):
        response = self.client.delete('/domains/%d/tsigkeys/foobar' % self.domain_id)
        self.assert404(response)


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
