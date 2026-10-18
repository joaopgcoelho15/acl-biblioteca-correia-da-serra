import unittest
from html.parser import HTMLParser
from server import app as module


class Elements(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.elements = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class MobileMarkupTests(unittest.TestCase):
    def test_home_links_open_the_requested_index(self):
        response = module.app.test_client().get('/')
        elements = Elements(response.get_data(as_text=True)).elements
        links = [attrs['href'] for tag, attrs in elements if tag == 'a' and attrs.get('class') == 'browse-tile']
        self.assertEqual(len(links), 4)
        for index, link in zip(['classification', 'author', 'local_atual', 'date'], links):
            self.assertIn(f'index={index}', link)

    def test_filters_have_search_labels_and_translated_dialog_controls(self):
        client = module.app.test_client()
        for lang, done, close in [('pt', 'Concluir', 'Fechar'), ('en', 'Done', 'Close')]:
            with self.subTest(lang=lang):
                response = client.get('/catalogo', query_string={'lang': lang})
                self.assertEqual(response.status_code, 200)
                elements = Elements(response.get_data(as_text=True)).elements
                selects = [attrs for tag, attrs in elements if tag == 'select' and 'data-search-label' in attrs]
                self.assertEqual(len(selects), len(module.FILTERS))
                self.assertTrue(all(select['data-done-label'] == done and select['data-close-label'] == close for select in selects))
                self.assertTrue(all('multiple' in select for select in selects))
                details = [attrs for tag, attrs in elements if tag == 'details' and attrs.get('class') == 'filters-disclosure']
                self.assertEqual(len(details), 1)
                self.assertIn('open', details[0])

    def test_navigation_enhancement_is_available_on_content_and_detail_pages(self):
        client = module.app.test_client()
        for route in ['/sobre', '/investigacao', '/contactos', '/obra/1252']:
            with self.subTest(route=route):
                response = client.get(route)
                self.assertEqual(response.status_code, 200)
                html = response.get_data(as_text=True)
                self.assertIn('aria-controls="site-navigation"', html)
                self.assertIn('navigation.js', html)


if __name__ == '__main__':
    unittest.main()
