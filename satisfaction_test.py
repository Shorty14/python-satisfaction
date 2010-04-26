import os
import unittest2 as unittest

import mock

import satisfaction


def urlopen_404(url):
    headers = mock.Mock()
    headers.getheader.return_value = '404'
    response = mock.Mock()
    response.headers = headers
    return response
    

def feedparser_404(url):
    return {'status': 404}


class TestHelper(unittest.TestCase):
    
    def stub_method(self, cls, name, stub):
        original = getattr(cls, name)
        self.original_methods.append((cls, original))
        setattr(cls, name, stub)
    
    def setUp(self):
        self.original_urls = []
        self.original_methods = []
        if hasattr(self, 'withFixtures'):
            self.withFixtures()

        if len(self.original_methods) == 0:
            def url_for_page(self, page):
                return '%s-page-%s.xml' % (self.url.rsplit('.', 1)[0], page)
            self.stub_method(satisfaction.AtomParser, 'url_for_page', url_for_page)
        
            def child_url(self, resource):
                return '%s-%s.xml' % (self.url().rsplit('.', 1)[0], resource)
            self.stub_method(satisfaction.Resource, 'child_url', child_url)
    
    def tearDown(self):
        if hasattr(self, 'real_atom_url_func'):
            satisfaction.AtomParser.url_for_page = self.real_atom_url_func
        if hasattr(self, 'original_methods'):
            for cls, method in self.original_methods:
                setattr(cls, method.__name__, method)
        if hasattr(self, 'original_urls'):
            for cls, url in self.original_urls:
                cls.URL = url
    
    def useFixture(self, stubbed_cls, name=None):
        self.original_urls.append((stubbed_cls, stubbed_cls.URL))
        base = stubbed_cls.__name__.lower()
        filename = '%s-%s.xml' % (base, name) if name else '%s.html' % base
        stubbed_cls.URL = os.path.join(os.getcwd(), 'fixtures', filename)
    
    def product(self):
        return satisfaction.Product('1234')

    def topic(self):
        return satisfaction.Topic('1234')


class MissingProductTest(TestHelper):
    
    @mock.patch('urllib.urlopen', urlopen_404)
    def test_product_not_found(self):
        with self.assertRaises(satisfaction.ResourceNotFound):
            self.product().title


class ProductWithTopicsTest(TestHelper):
    
    def withFixtures(self):
        self.useFixture(satisfaction.Product)
    
    def test_can_retrieve_title(self):
        self.assertEqual('Wordtracker Keywords', self.product().title)
    
    @unittest.skip('pending instantiation of topic from data')
    def test_can_retrieve_topics(self):
        self.assertEqual(3, self.product().topic_count)
        self.assertEqual(3, len(list(self.product().topics)))
        self.assertIsInstance(list(self.product().topics)[0], satisfaction.Topic)


class MissingTopicTest(TestHelper):

    @mock.patch('feedparser.parse', feedparser_404)
    def test_topic_not_found(self):
        with self.assertRaises(satisfaction.ResourceNotFound):
            self.topic().title
    

class TopicWithoutRepliesTest(TestHelper):
    
    def withFixtures(self):
        self.useFixture(satisfaction.Topic, 'without-replies')

    def test_title_available(self):
        self.assertEqual('Fantastic improvement', self.topic().title)
    
    def test_content_available(self):
        self.assertIn('Well done!', self.topic().content)
    
    def test_no_replies_found(self):
        self.assertEqual(0, self.topic().reply_count)
        self.assertEqual(0, len(list(self.topic().replies)))


class TopicWithRepliesTest(TestHelper):
    
    def withFixtures(self):
        self.useFixture(satisfaction.Topic, 'with-replies')
    
    def test_replies_found(self):
        self.assertEqual(3, self.topic().reply_count)
        self.assertEqual(3, len(list(self.topic().replies)))
    
    def test_topic_not_included_in_replies(self):
        extract_content = lambda reply: reply.content[0]['value']
        reply_messages = map(extract_content, self.topic().replies)
        self.assertNotIn(self.topic().content, reply_messages)


class TopicWithMultiplePagesOfRepliesTest(TestHelper):
    
    def withFixtures(self):
        self.useFixture(satisfaction.Topic, 'with-lots-of-replies')
    
    def test_replies_found(self):
        self.assertEqual(95, self.topic().reply_count)
        self.assertEqual(95, len(list(self.topic().replies)))


if __name__ == '__main__':
    unittest.main()
