import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_catalog_integrity import validate  # noqa: E402


class CatalogIntegrityTests(unittest.TestCase):
    def test_catalog_integrity_passes(self):
        self.assertEqual(validate(), [])


if __name__ == "__main__":
    unittest.main()
