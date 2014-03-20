from . import DBTestCase

from poff.models import Domain

class DispatchTest(DBTestCase):

    def set_up(self):
        domain = Domain(name='test.com')
        self.domain_id, = self.add_objects(domain)


    def test_post_rewrite(self):
        data = {'_method': 'DELETE'}
        #self.assert200(self.client.delete('/domains/%d' % self.domain_id, follow_redirects=True))
        response = self.client.post('/domains/%d' % self.domain_id, data=data, follow_redirects=True)
        self.assert200(response)
