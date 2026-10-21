import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('profile_reader', Path(__file__).parents[1] / 'scripts/read-profile.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


class ProfileTests(unittest.TestCase):
    def test_permission_is_not_absence(self):
        with patch.object(Path, 'read_text', side_effect=PermissionError('private detail')):
            self.assertEqual(reader.read_profile('profile.json'), {'status': 'access_denied'})

    def test_missing(self):
        with patch.object(Path, 'read_text', side_effect=FileNotFoundError()):
            self.assertEqual(reader.read_profile('profile.json'), {'status': 'not_found'})

    def test_other_read_error(self):
        with patch.object(Path, 'read_text', side_effect=OSError('private detail')):
            self.assertEqual(reader.read_profile('profile.json'), {'status': 'read_error'})

    def read(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'profile.json'
            path.write_text(json.dumps(data), encoding='utf-8')
            return reader.read_profile(path)

    def test_confirmed_projection_excludes_unrelated_fields(self):
        data = {'version': 1, 'active_project': 'owner/repo', 'unrelated': 'excluded', 'projects': {'owner/repo': {'branch': 'main', 'repository_confirmed': True, 'member': {'display_name': 'Example', 'confirmed': True}, 'extra': 'excluded'}}}
        result = self.read(data)
        self.assertEqual(result['member']['display_name'], 'Example')
        self.assertNotIn('excluded', json.dumps(result))

    def test_unconfirmed_does_not_restore(self):
        self.assertEqual(self.read({'version': 1, 'active_project': 'owner/repo', 'projects': {'owner/repo': {'repository_confirmed': False}}}), {'status': 'unbound'})

    def test_unknown_schema(self):
        self.assertEqual(self.read({'version': 2}), {'status': 'unsupported_schema'})

    def test_invalid_json(self):
        with patch.object(Path, 'read_text', return_value='{'):
            self.assertEqual(reader.read_profile('profile.json'), {'status': 'invalid_profile'})


if __name__ == '__main__':
    unittest.main()
