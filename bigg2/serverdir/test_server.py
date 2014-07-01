import server2
import tornado.ioloop
from tornado.httpclient import AsyncHTTPClient
from tornado.testing import AsyncHTTPTestCase, gen_test

class TestBuilder(AsyncHTTPTestCase):
	def get_app(self):
		return server2.application
	def test_request(self):
		response = self.fetch('/about.html')
		
def test_server():
	tornado.ioloop.IOLoop.instance().add_timeout(100, escher.server.stop())
	escher.server.run(port=8881)
	print 'stopped'