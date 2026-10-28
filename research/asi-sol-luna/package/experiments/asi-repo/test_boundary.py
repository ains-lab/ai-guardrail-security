import tempfile
import unittest
from pathlib import Path
from repo_lab import safe_path

class BoundaryTests(unittest.TestCase):
    def test_scope(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as d:
            root=Path(d)
            self.assertEqual(safe_path(root, 'settings.json'), root/'settings.json')
            for p in ('../escape', '/etc/passwd'):
                with self.assertRaises(ValueError): safe_path(root,p)
            (root/'link').symlink_to(root.parent, target_is_directory=True)
            with self.assertRaises(ValueError): safe_path(root,'link/escape')

if __name__=='__main__': unittest.main()
