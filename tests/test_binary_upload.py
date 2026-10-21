import copy
import hashlib
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).parents[1]
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

packet_api = load('packet_binary_test', 'scripts/prepare-work-sync.py')
upload = load('upload_binary_test', 'scripts/upload-work-sync.py')


class BinaryUploadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def packet(self, suffix='.docx'):
        self.source = self.root / ('result' + suffix)
        self.source.write_bytes(b'PK\x03\x04\x00\xff\r\nraw fixture bytes')
        draft = dict(request_key='binary-fixture', author='Fixture Member', stage='Fixture', topic='Fixture',
                     kind='decision', work=['Fixture only'], conclusions=['Local test'],
                     artifacts=[{'path': str(self.source)}])
        return packet_api.prepare(draft)

    def test_formats_raw_manifest_and_stable_id(self):
        for suffix in ('.docx', '.pdf', '.pptx', '.png', '.jpg', '.jpeg', '.gif', '.webp'):
            packet = self.packet(suffix)
            self.assertEqual(len(packet['files']), 1)
            self.assertEqual(packet['binary_files'][0]['sha256'], hashlib.sha256(self.source.read_bytes()).hexdigest())
            self.assertEqual(upload.payload(packet)[packet['binary_files'][0]['path']], self.source.read_bytes())
        old = self.packet()
        draft = dict(request_key='binary-fixture', author='Fixture Member', stage='Fixture', topic='Fixture',
                     kind='decision', work=['Revised fixture'], conclusions=['Local test'], artifacts=[{'path':str(self.source)}])
        new = packet_api.prepare(draft, old)
        self.assertEqual(old['submission_id'], new['submission_id'])
        self.assertNotEqual(old['request_fingerprint'], new['request_fingerprint'])

    def test_confirmation_target_member_and_source_change_guards(self):
        packet = self.packet()
        value = upload.plan(packet, 'example/fixture', 'main', 'Fixture Member')
        self.assertEqual(upload.execute(value, 'wrong')['status'], 'confirmation_required')
        with self.assertRaises(ValueError):
            upload.plan(packet, 'example/fixture', 'main', 'Other Member')
        with self.assertRaises(ValueError):
            upload.plan(packet, 'example/fixture', '../escape', 'Fixture Member')
        self.source.write_bytes(b'changed')
        with self.assertRaises(ValueError):
            upload.execute(value, value['confirmation_sha256'])

    def test_packet_manifest_path_and_cancel_guards(self):
        packet = self.packet()
        bad = copy.deepcopy(packet)
        bad['artifact_manifest'][0]['sha256'] = '0' * 64
        with self.assertRaises(ValueError): upload.payload(bad)
        bad = copy.deepcopy(packet)
        bad['files'][0]['path'] = '../outside.md'
        with self.assertRaises(ValueError): upload.payload(bad)
        packet['state'] = 'cancelled'
        with self.assertRaises(ValueError): upload.payload(packet)

    def test_local_git_bytes_roundtrip_duplicate_and_conflict(self):
        # Only self-created local Git repositories; no GitHub URL or auth.
        packet = self.packet()
        files = upload.payload(packet)
        env = os.environ.copy()
        env.update(GIT_AUTHOR_NAME='Fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
                   GIT_COMMITTER_NAME='Fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid')
        paths = [self.root / x for x in ('work', 'remote.git', 'reader')]
        for p in paths: p.mkdir()
        git = upload.Git(paths[0], env); git.init()
        oid = git.run('hash-object', '-w', '--stdin', data=b'existing\r\n').decode().strip()
        git.run('update-index', '--add', '--cacheinfo', '100644', oid, 'README.md')
        tree = git.run('write-tree').decode().strip()
        initial = git.run('commit-tree', tree, data=b'Fixture seed\n').decode().strip()
        commit = upload.stage(git, initial, files, packet['submission_id'])
        bare = upload.Git(paths[1], env); bare.run('init', '--bare', '--quiet', '--template=')
        git.run('push', '--quiet', str(paths[1]), initial + ':refs/heads/main')
        git.run('push', '--quiet', str(paths[1]), commit + ':refs/heads/main')
        reader = upload.Git(paths[2], env); reader.init()
        reader.run('fetch', '--quiet', '--depth=1', str(paths[1]), 'refs/heads/main')
        received = reader.run('rev-parse', 'FETCH_HEAD').decode().strip()
        self.assertEqual(received, commit)
        checks = upload.remote_files(reader, received, files)
        self.assertTrue(all(x['status'] == 'verified' for x in checks))
        self.assertEqual(reader.run('cat-file', 'blob', reader.tree(received)['README.md'][2]), b'existing\r\n')
        self.assertIsNone(upload.stage(reader, received, files, packet['submission_id']))
        altered = dict(files); altered[next(iter(altered))] += b'changed'
        with self.assertRaises(ValueError): upload.stage(reader, received, altered, packet['submission_id'])
        self.assertTrue(any(x['status'] == 'different' for x in upload.remote_files(reader, received, altered)))


if __name__ == '__main__':
    unittest.main()
