from . import DBTestCase
from poff.models import Domain

class DomainTest(DBTestCase):

    def set_up(self):
        domain = Domain(name='example.com')
        self.domain_id, = self.add_objects(domain)


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
