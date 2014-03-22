from . import DBTestCase
from poff.models import Domain, Record

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


    def test_delete_domain(self):
        response = self.client.delete('/domains/%d' % self.domain_id, follow_redirects=True)
        self.assert200(response)
        with self.app.app_context():
            domains = Domain.query.all()
            self.assertEqual(len(domains), 0)

            # associated records should have been cascade deleted
            records = Record.query.all()
            self.assertEqual(len(records), 0)
