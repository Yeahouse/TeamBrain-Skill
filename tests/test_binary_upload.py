import copy
import hashlib
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import json

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

    def observation(self, files, omitted=(), unreadable=(), extras=None):
        class Observation:
            def __init__(inner):
                inner.calls = []
                inner.data = {str(i): raw for i, raw in enumerate(files.values())}
                inner.entries = {p: ('100644', 'blob', str(i)) for i, p in enumerate(files) if p not in omitted}
                inner.entries.update(extras or {})
            def init(inner): pass
            def tree(inner, commit): return inner.entries
            def run(inner, *args, data=None):
                inner.calls.append(args)
                if args[0] in ('fetch', 'remote'): return b''
                if args[0] == 'rev-parse': return b'a' * 40
                if args[0] == 'cat-file':
                    if args[2] in unreadable: raise upload.GitFailure('controlled blob failure')
                    return inner.data[args[2]]
                raise AssertionError('Unexpected write or identity operation')
        return Observation()

    def test_per_file_partial_results_do_not_erase_success(self):
        files = {'records/id/record.md': b'record', 'records/id/artifacts/a.txt': b'text', 'records/id/artifacts/b.docx': b'binary'}
        fake = self.observation(files, omitted=['records/id/artifacts/a.txt'], unreadable=['2'])
        manifest = [{'path': p, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'kind': kind}
                    for (p, raw), kind in zip(files.items(), ('record', 'text', 'binary'))]
        result = upload.inspect_files(fake, 'a' * 40, manifest)
        self.assertEqual([x['status'] for x in result], ['verified', 'missing', 'unknown'])
        self.assertIn('remote_sha256', result[0])
        self.assertEqual([x['kind'] for x in result], ['record', 'text', 'binary'])

    def test_duplicate_and_partial_stop_before_identity_or_push(self):
        packet = self.packet(); value = upload.plan(packet, 'example/fixture', 'main', 'Fixture Member')
        files = upload.payload(packet); fake = self.observation(files)
        with patch.object(upload, 'Git', side_effect=AssertionError('Receipt required before network')):
            self.assertEqual(upload.execute(value, value['confirmation_sha256'])['status'], 'receipt_path_required')
        receipt = self.root / 'attempt.receipt.json'
        with patch.object(upload, 'Git', return_value=fake):
            result = upload.execute(value, value['confirmation_sha256'], receipt)
        self.assertEqual(result['status'], 'already_present_verified')
        self.assertFalse(result['remote_write_attempted'])
        with patch.object(upload, 'Git', side_effect=AssertionError('Must stop before any connection')):
            self.assertEqual(upload.execute(value, value['confirmation_sha256'], receipt)['status'], 'prior_attempt_inspect_remote_before_retry')
        fake = self.observation(files, omitted=[packet['binary_files'][0]['path']])
        with patch.object(upload, 'Git', return_value=fake):
            result = upload.execute(value, value['confirmation_sha256'], self.root / 'partial.receipt.json')
        self.assertEqual(result['status'], 'conflict_or_partial_stop')
        self.assertEqual([x['status'] for x in result['files']], ['verified', 'missing'])
        self.assertFalse(any(x[0] in ('push', 'config') for x in fake.calls))

    def test_readonly_recovery_without_local_source_and_extra_collision(self):
        packet = self.packet(); value = upload.plan(packet, 'example/fixture', 'main', 'Fixture Member')
        files = upload.payload(packet); self.source.unlink()
        fake = self.observation(files)
        with patch.object(upload, 'Git', return_value=fake):
            result = upload.inspect_remote(value)
        self.assertEqual(result['status'], 'verified')
        self.assertFalse(result['remote_write_attempted'])
        self.assertEqual(result['member'], 'Fixture Member')
        extra = 'records/' + packet['submission_id'].upper() + '/artifacts/other.txt'
        fake.entries[extra] = ('100644', 'blob', 'unused')
        result = upload.check_remote(fake, 'a' * 40, value)
        self.assertEqual(result['status'], 'conflict_or_partial_stop')
        self.assertIn(extra, result['extra_record_paths'])
        fake = self.observation({}, extras={'records': ('120000', 'blob', 'unused')})
        result = upload.check_remote(fake, 'a' * 40, value)
        self.assertEqual(result['status'], 'conflict_or_partial_stop')
        self.assertEqual(result['blocking_parent_paths'], ['records'])

    def test_interruption_keeps_write_intent_and_blocks_blind_replay(self):
        packet = self.packet(); value = upload.plan(packet, 'example/fixture', 'main', 'Fixture Member')
        fake = self.observation({}); original = fake.run
        def run(*args, data=None):
            if args[0] == 'config': return b'fixture identity'
            if args[0] == 'ls-remote': return b'a' * 40 + b' refs/heads/main'
            if args[0] == 'push': raise KeyboardInterrupt('controlled interruption')
            return original(*args, data=data)
        fake.run = run; receipt = self.root / 'interrupted.receipt.json'
        with patch.object(upload, 'Git', return_value=fake), patch.object(upload, 'stage', return_value='b' * 40):
            with self.assertRaises(KeyboardInterrupt): upload.execute(value, value['confirmation_sha256'], receipt)
        saved = json.loads(receipt.read_text(encoding='utf-8'))
        self.assertEqual(saved['status'], 'write_intent_outcome_unknown')
        self.assertEqual(saved['submission_id'], packet['submission_id'])
        self.assertEqual(saved['confirmation_sha256'], value['confirmation_sha256'])
        self.assertEqual(len(saved['files']), 2)
        self.assertEqual(upload.execute(value, value['confirmation_sha256'], receipt)['status'], 'prior_attempt_inspect_remote_before_retry')


if __name__ == '__main__':
    unittest.main()
