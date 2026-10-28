import unittest
from repo_lab import matrix_cases

class MatrixTests(unittest.TestCase):
    def test_balanced_single_variable_conditions(self):
        cases=matrix_cases()
        self.assertEqual(len(cases),12)
        self.assertEqual(len({c[0] for c in cases}),12)
        for repetition in range(1,4):
            by_name={name:(doc,explicit) for name,doc,explicit in cases if name.endswith('_'+str(repetition))}
            self.assertEqual(len(by_name),4)
            self.assertEqual(by_name[f'explicit_clean_{repetition}'][0],by_name[f'general_clean_{repetition}'][0])
            self.assertEqual(by_name[f'explicit_poisoned_{repetition}'][0],by_name[f'general_poisoned_{repetition}'][0])
            self.assertTrue(by_name[f'explicit_clean_{repetition}'][1])
            self.assertFalse(by_name[f'general_clean_{repetition}'][1])

if __name__=='__main__': unittest.main()
