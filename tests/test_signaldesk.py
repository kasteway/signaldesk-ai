import json
import unittest
from signaldesk.core import analyze, load_rows
from signaldesk.brief import answer, cards, retrieve
from signaldesk.mcp_server import handle
from signaldesk.sql_check import run as sql_run

class SignalDeskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = analyze(load_rows())

    def test_dataset_scope_and_mix(self):
        self.assertEqual(self.data['total'], 7953)
        self.assertEqual(sum(i['count'] for i in self.data['weeks']), 7953)
        self.assertEqual(sum(i['count'] for i in self.data['sub_products']), 7953)
        self.assertEqual(self.data['issues'][0], {'name':'Fraud or scam','count':2929})

    def test_signal_thresholds(self):
        for s in self.data['signals']:
            self.assertGreaterEqual(s['observed'], 10)
            self.assertGreaterEqual(s['baseline'], 5)
            self.assertGreaterEqual(s['score'], 3)
            self.assertGreaterEqual(s['observed']/s['baseline'], 1.4)
            self.assertGreaterEqual(s['week'], '2024-01-29')

    def test_retrieval_grounding(self):
        hits = retrieve('fraud scam', cards(self.data))
        self.assertEqual(hits[0]['id'], 'issue:Fraud or scam')
        reply = answer('fraud scam')
        self.assertIn('2,929', reply['answer'])
        self.assertIn('web/dashboard.json', reply['citations'])
        self.assertFalse(answer('quantum banana')['citations'])

    def test_sql_matches_python(self):
        self.assertEqual(sql_run()[0], ("Fraud or scam", 2929))

    def test_mcp_tools(self):
        init = handle({'jsonrpc':'2.0','id':1,'method':'initialize','params':{}})
        self.assertEqual(init['result']['serverInfo']['name'], 'signaldesk-ai')
        listed = handle({'jsonrpc':'2.0','id':2,'method':'tools/list'})
        self.assertEqual(len(listed['result']['tools']), 3)
        called = handle({'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'get_overview','arguments':{}}})
        self.assertEqual(json.loads(called['result']['content'][0]['text'])['total'], 7953)

if __name__ == '__main__': unittest.main()
