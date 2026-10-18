import unittest
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch
import pandas as pd
from server import app as module


class FacetTests(unittest.TestCase):
    def setUp(self):
        rows=[]
        for author,year,place,title in [('Alice','1500','Paris','Alpha'),('Bruno','1600','Rome','Beta'),('Carlos','1500','Rome','Gamma'),('','1500','Paris','Delta')]:
            row={meta['field']:'' for meta in module.FILTERS}
            row.update(author=author,date=year,titulo=title,**{'local(atual)':place})
            rows.append(row)
        self.df=pd.DataFrame(rows)
        self.context=module.app.test_request_context('/catalogo?lang=pt')
        self.context.push()

    def tearDown(self):
        self.context.pop()

    def options(self,selected,query=''):
        return {key:{i['value']:i for i in values} for key,values in module.facet_options(self.df,selected,query).items()}

    def test_unselected_counts_match_global(self):
        options=self.options({})
        self.assertEqual(options['date']['1500']['count'],3)
        self.assertTrue(all(i['available'] for values in options.values() for i in values.values()))

    def test_date_disables_incompatible_authors(self):
        options=self.options({'date':'1500'})
        self.assertTrue(options['author']['Alice']['available'])
        self.assertFalse(options['author']['Bruno']['available'])
        self.assertEqual(options['author']['Bruno']['count'],0)
        self.assertEqual(options['author']['Bruno']['total'],1)
        self.assertTrue(options['author']['_sem_valor']['available'])

    def test_own_facet_is_not_restricted_by_its_selection(self):
        options=self.options({'author':'Alice'})
        self.assertTrue(options['author']['Bruno']['available'])
        self.assertFalse(options['date']['1600']['available'])

    def test_combined_filters(self):
        options=self.options({'date':'1500','local_atual':'Paris'})
        self.assertFalse(options['author']['Carlos']['available'])
        self.assertTrue(options['local_atual']['Rome']['available'])
        self.assertEqual(options['local_atual']['Rome']['count'],1)
        self.assertEqual(options['local_atual']['Rome']['total'],2)

    def test_totals_are_stable_for_query_and_missing_values(self):
        before=self.options({})
        after=self.options({'date':'1500'},'Alpha')
        for key,values in before.items():
            for value,option in values.items():
                self.assertEqual(option['total'],after[key][value]['total'])
                self.assertLessEqual(after[key][value]['count'],option['total'])

    def test_individual_removal_preserves_others_and_resets_page(self):
        with module.app.test_request_context('/catalogo?author=Alice&date=1500&q=Alpha&sort=title_desc&page=3&lang=en'):
            items=module.active_filter_items({'author':'Alice','date':'1500'},'Alpha')
        self.assertEqual(len(items),3)
        params=parse_qs(urlsplit(items[0]['url']).query)
        self.assertNotIn('author',params)
        self.assertNotIn('page',params)
        self.assertEqual(params['date'],['1500'])
        self.assertEqual(params['q'],['Alpha'])
        self.assertEqual(params['sort'],['title_desc'])
        self.assertEqual(params['lang'],['en'])

    def test_free_text_restricts_all_facets(self):
        options=self.options({},'Beta')
        self.assertFalse(options['date']['1500']['available'])
        self.assertTrue(options['author']['Bruno']['available'])

    def test_empty_matches_keeps_all_options_visible(self):
        options=self.options({},'nonexistent')
        self.assertEqual(len(options['author']),4)
        self.assertFalse(any(i['available'] for values in options.values() for i in values.values()))

    def test_missing_value_filter(self):
        self.assertEqual(len(module.apply_filters(self.df,{'author':'_sem_valor'})),1)

    def test_api_uses_same_counts(self):
        with patch.object(module,'load_data',return_value=self.df):
            response=module.app.test_client().get('/catalogo/opcoes?date=1500&lang=en')
        self.assertEqual(response.status_code,200)
        options={i['value']:i for i in response.json['options']['author']}
        self.assertFalse(options['Bruno']['available'])


class RealWorkbookTests(unittest.TestCase):
    def test_all_ids_and_images_preserved(self):
        df=module.load_data()
        self.assertEqual(len(df),1869)
        self.assertEqual(df.id.nunique(),1869)
        self.assertTrue(set(module.work_image_manifest()).issubset({str(i) for i in df.id}))

    def test_date_ranges_remain_options(self):
        with module.app.test_request_context('/catalogo'):
            options=module.facet_options(module.load_data(),{})['date']
        self.assertIn('1770-1777',{i['value'] for i in options})

    def test_pt_eng_routes_sorting_and_page_validation(self):
        client=module.app.test_client()
        for lang in ['pt','en']:
            for path in ['/catalogo?date=1500','/catalogo?q=Seneca','/catalogo?page=invalid','/catalogo?sort=title_desc','/obra/1737']:
                with self.subTest(lang=lang,path=path):
                    response=client.get(path+('&' if '?' in path else '?')+'lang='+lang)
                    self.assertEqual(response.status_code,200)


if __name__=='__main__':
    unittest.main()
