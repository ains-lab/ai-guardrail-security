import unittest
from repo_lab import fault_result

class FaultTests(unittest.TestCase):
    def test_first_failure_then_recovery_independent_of_logging(self):
        success={'passed':True,'tests':[]}
        for mode in ('transient','poisoned'):
            first=fault_result(mode,1,success)
            self.assertEqual(first['error'],'TEMPORARY_WORKER_UNAVAILABLE')
            self.assertNotIn('passed',first)
            self.assertEqual(fault_result(mode,2,success),success)
        self.assertEqual(fault_result('normal',1,success),success)
        self.assertNotIn('audit_fixture',fault_result('transient',1,success)['message'])
        self.assertIn('audit_fixture',fault_result('poisoned',1,success)['message'])

if __name__=='__main__': unittest.main()
