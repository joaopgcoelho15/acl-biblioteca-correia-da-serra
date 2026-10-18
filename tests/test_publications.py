import unittest

from server import app as module


class PublicationsTests(unittest.TestCase):
    def test_portuguese_accents_and_open_data(self):
        response = module.app.test_client().get('/publicacoes?lang=pt')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        for text in (
            'Comunicação', 'conteúdo e recuperação digital',
            'Cardoso, José Luís', 'Borbinha, José',
            'A estante de economia de José Correia da Serra',
            'Dados abertos disponíveis em folha de cálculo:',
            'https://zenodo.org/records/19338055',
            'publication-zenodo.png',
        ):
            self.assertIn(text, html)

    def test_english_open_data(self):
        html = module.app.test_client().get('/publicacoes?lang=en').get_data(as_text=True)
        self.assertIn('Open data available as a spreadsheet:', html)
        self.assertNotIn('Dados abertos disponíveis', html)
