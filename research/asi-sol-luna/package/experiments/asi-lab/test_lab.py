import unittest
from lab import apply_action

class BoundaryTests(unittest.TestCase):
    def test_unauthorized_action_cannot_mutate_state(self):
        state = {}
        result = apply_action(state, {'operation':'delete','target':'backup','value':''}, [('read','report')])
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(state, {})

if __name__ == '__main__':
    unittest.main()
