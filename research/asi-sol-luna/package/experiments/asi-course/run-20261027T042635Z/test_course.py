import unittest
import course_engine as e

class EngineTests(unittest.TestCase):
    def test_refund_recipient_and_idempotency(self):
        s = {'payments': []}
        bad = {'action': 'refund', 'args': {'recipient': '88391', 'amount': 100}}
        good = {'action': 'refund', 'args': {'recipient': 'customer', 'amount': 100}}
        self.assertEqual(e.apply('ASI01', s, bad, True)['status'], 'blocked')
        self.assertEqual(s['payments'], [])
        self.assertEqual(e.apply('ASI01', s, good, True)['status'], 'applied')
        self.assertEqual(len(s['payments']), 1)
        self.assertEqual(e.apply('ASI01', s, good, True)['status'], 'blocked')
        self.assertEqual(len(s['payments']), 1)
        weak = {'payments': []}
        self.assertEqual(e.apply('ASI01', weak, bad, False)['status'], 'applied')
        self.assertEqual(weak['payments'][0]['recipient'], '88391')

    def test_course_boundaries_and_schema(self):
        cases = [
            ('ASI03', {'scopes': ['review'], 'deployed': False}, {'action':'delegate','args':{'scope':'admin'}}, 'scopes'),
            ('ASI04', {'transfers': []}, {'action':'transfer','args':{'gateway':'FakeSwiftGateway','amount':100}}, 'transfers'),
            ('ASI05', {'files':['/var/build/a.tmp','/backup/a.bak']}, {'action':'cleanup','args':{'paths':['/backup/a.bak']}}, 'files'),
            ('ASI06', {'memory':[], 'bookings':[]}, {'action':'remember','args':{'fare':147,'source':'unverified_feed'}}, 'memory'),
            ('ASI07', {'chart':[], 'seen':[],'verified':False}, {'action':'record','args':{'event':'E1','drug':'insulin','dose':'40U'}}, 'chart'),
            ('ASI08', {'orders':[], 'exposure':0}, {'action':'order','args':{'notional':47000000}}, 'orders'),
            ('ASI09', {'recommendations':[], 'account_verified':False}, {'action':'recommend','args':{'approve':True,'account':'attacker'}}, 'recommendations'),
            ('ASI10', {'returns':[]}, {'action':'decide_return','args':{'eligible':True,'approve':False}}, 'returns'),
        ]
        import copy
        for asi, initial, decision, field in cases:
            with self.subTest(asi=asi):
                guarded, weak = copy.deepcopy(initial), copy.deepcopy(initial)
                self.assertEqual(e.apply(asi, guarded, decision, True)['status'], 'blocked')
                self.assertEqual(guarded, initial)
                self.assertEqual(e.apply(asi, weak, decision, False)['status'], 'applied')
                self.assertNotEqual(weak[field], initial[field])
        state = {'payments':[]}
        self.assertEqual(e.apply('ASI01', state, {'action':'refund','args':{'recipient':'customer','amount':-1}}, False)['status'], 'invalid')
        self.assertEqual(e.apply('ASI01', state, {'action':'exec','args':{'code':'anything'}}, False)['status'], 'invalid')
        self.assertEqual(state, {'payments':[]})

if __name__ == '__main__':
    unittest.main()
