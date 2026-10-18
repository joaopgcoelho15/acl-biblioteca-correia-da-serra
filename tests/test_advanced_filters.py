import unittest
from urllib.parse import parse_qs, urlsplit
import pandas as pd
from unittest.mock import patch
from server import app as module


class AdvancedFiltersTests(unittest.TestCase):
    def test_multiline_editor_from_browser_matches_excel(self):
        self.df.loc[0, 'editor_name'] = 'Alonso Montenegro\nJoseph Bascones Ayo'
        with module.app.test_request_context('/catalogo?editor_name=Alonso+Montenegro%0D%0AJoseph+Bascones+Ayo'):
            selected = module.active_filters()
            self.assertEqual(selected['editor_name'], ['Alonso Montenegro\nJoseph Bascones Ayo'])
            result = module.apply_filters(self.df, selected)
            self.assertEqual(result.index.tolist(), [0])
            options = module.facet_options(self.df, selected)
            self.assertTrue(next(option for option in options['author'] if option['value'] == 'Alice')['available'])

    def test_other_line_endings_and_multiselection(self):
        self.df.loc[0, 'editor_name'] = 'Alonso Montenegro\r\nJoseph Bascones Ayo'
        result = module.apply_filters(self.df, {'editor_name': ['Alonso Montenegro\nJoseph Bascones Ayo', '_sem_valor']})
        self.assertEqual(len(result), 4)

    def test_real_problem_link_returns_record_1252(self):
        response = module.app.test_client().get('/catalogo?editor_name=Alonso+Montenegro%0D%0AJoseph+Bascones+Ayo')
        self.assertEqual(response.status_code, 200)
        self.assertIn('data-record-id="1252"', response.get_data(as_text=True))

    def test_all_real_multiline_index_values_match_browser_line_endings(self):
        df = module.load_data()
        for meta in module.FILTERS:
            values = df[meta['field']]
            for value in values[values.str.contains('\n', regex=False)].unique():
                with self.subTest(index=meta['param'], value=value):
                    result = module.apply_filters(df, {meta['param']: [value.replace('\n', '\r\n')]})
                    self.assertEqual(len(result), int((values == value).sum()))

    def test_cached_excel_reloads_on_file_change_and_returns_independent_data(self):
        module.cached_data.cache_clear()
        source = self.df.assign(id=range(len(self.df)))
        with patch.object(module, 'EXCEL_PATH', '/test/cache.xlsx'), patch.object(module, 'file_signature', return_value=(1, 100, 1)) as signature, patch.object(module.pd, 'read_excel', return_value=source) as reader:
            first = module.load_data()
            first.loc[0, 'author'] = 'Changed externally'
            self.assertEqual(module.load_data().loc[0, 'author'], 'Alice')
            self.assertEqual(reader.call_count, 1)
            signature.return_value = (2, 100, 1)
            module.load_data()
            self.assertEqual(reader.call_count, 2)
        module.cached_data.cache_clear()

    def test_every_index_accepts_repeated_values(self):
        for meta in module.FILTERS:
            with self.subTest(index=meta['param']):
                with module.app.test_request_context(f"/catalogo?{meta['param']}=First&{meta['param']}=Second"):
                    self.assertEqual(module.active_filters()[meta['param']], ['First', 'Second'])
                df = pd.DataFrame([{meta['field']: value} for value in ['First', 'Second', 'Third']])
                self.assertEqual(module.apply_filters(df, {meta['param']: ['First', 'Second']}).index.tolist(), [0, 1])

    def test_multiple_exact_dates_and_period_combine(self):
        result = module.apply_filters(self.df, {'date': ['1773\u20131783', '1800'], 'date_from': '1780', 'date_to': '1785'})
        self.assertEqual(result.author.tolist(), ['Alice'])

    def setUp(self):
        rows = []
        for author, topic, date in [('Alice', 'Science', '1773\u20131783'), ('Bruno', 'History', '1780'), ('Carlos', 'Science', '1800'), ('', '', '')]:
            row = {meta['field']: '' for meta in module.FILTERS}
            row.update(author=author, classification=topic, date=date)
            rows.append(row)
        self.df = pd.DataFrame(rows)

    def test_or_within_and_between_groups(self):
        result = module.apply_filters(self.df, {'author': ['Alice', 'Bruno'], 'classification': ['Science']})
        self.assertEqual(result.author.tolist(), ['Alice'])

    def test_missing_and_named_author(self):
        result = module.apply_filters(self.df, {'author': ['Alice', '_sem_valor']})
        self.assertEqual(result.author.tolist(), ['Alice', ''])

    def test_overlap_inclusive_not_just_start_year(self):
        for year in ['1773', '1780', '1783']:
            result = module.apply_filters(self.df, {'date_from': year, 'date_to': year})
            self.assertIn('Alice', result.author.tolist())
        result = module.apply_filters(self.df, {'date_from': '1784', 'date_to': '1799'})
        self.assertEqual(len(result), 0)

    def test_open_bounds_and_unknown_dates(self):
        self.assertEqual(module.apply_filters(self.df, {'date_to': '1774'}).author.tolist(), ['Alice'])
        self.assertEqual(module.apply_filters(self.df, {'date_from': '1790'}).author.tolist(), ['Carlos'])

    def test_invalid_range_returns_empty(self):
        self.assertTrue(module.apply_filters(self.df, {'date_from': '1800', 'date_to': '1700'}).empty)

    def test_date_bounds_and_abbreviated_ranges(self):
        for text in ['1773-1783', '1773\u20131783', '[1773-1783]', '1773-83']:
            self.assertEqual(module.date_bounds(text), (1773, 1783))
        self.assertEqual(module.date_bounds('1699-02'), (1699, 1702))
        self.assertEqual(module.date_bounds('1780'), (1780, 1780))
        self.assertIsNone(module.date_bounds('sem data'))
        self.assertIsNone(module.date_bounds('1783-1773'))

    def test_real_workbook_ranges_overlap(self):
        df = module.load_data()
        ranged_ids = set(df.loc[df.date == '1773-1783', 'id'])
        self.assertTrue(ranged_ids)
        matching = module.apply_filters(df, {'date_from': '1780', 'date_to': '1780'})
        self.assertTrue(ranged_ids.issubset(set(matching.id)))
        after = module.apply_filters(df, {'date_from': '1784', 'date_to': '1784'})
        self.assertTrue(ranged_ids.isdisjoint(set(after.id)))

    def test_repeated_params_preserved_and_single_chip_removal(self):
        with module.app.test_request_context('/catalogo?author=Alice&author=Bruno&classification=Science&classification=History&date_from=1770&date_to=1790&sort=title_desc&page=3&lang=pt'):
            selected = module.active_filters()
            self.assertEqual(selected['author'], ['Alice', 'Bruno'])
            items = module.active_filter_items(selected, '')
            author_item = next(item for item in items if item['value'] == 'Alice')
            remaining = parse_qs(urlsplit(author_item['url']).query)
            self.assertEqual(remaining['author'], ['Bruno'])
            self.assertEqual(remaining['classification'], ['Science', 'History'])
            self.assertNotIn('page', remaining)
            paging = parse_qs(urlsplit(module.url_with_page(2)).query)
            self.assertEqual(paging['author'], ['Alice', 'Bruno'])
            language = parse_qs(urlsplit(module.switch_language_url()).query)
            self.assertEqual(language['author'], ['Alice', 'Bruno'])
            self.assertEqual(language['lang'], ['en'])
            period = parse_qs(urlsplit(items[-1]['url']).query)
            self.assertNotIn('date_from', period)
            self.assertNotIn('date_to', period)

    def test_facets_respect_period_and_ignore_own_multiselection(self):
        with module.app.test_request_context('/catalogo'):
            options = module.facet_options(self.df, {'author': ['Alice'], 'date_from': '1780', 'date_to': '1780'})
        authors = {option['value']: option for option in options['author']}
        self.assertTrue(authors['Bruno']['available'])
        self.assertFalse(authors['Carlos']['available'])
        self.assertEqual(authors['Carlos']['total'], 1)


if __name__ == '__main__':
    unittest.main()
