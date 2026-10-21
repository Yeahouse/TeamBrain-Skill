import importlib.util
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('prepare_work_sync',Path(__file__).parents[1]/'scripts/prepare-work-sync.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class DraftPacketTests(unittest.TestCase):
    def draft(self):
        return dict(request_key='test-request',author='虚构成员',stage='Work Sync 测试',topic='虚构工作',kind='decision',work=['比较两种方案'],conclusions=['选择方案 B'])

    def test_stable_request_and_revision_require_confirmation(self):
        first=module.prepare(self.draft())
        revised=self.draft(); revised['conclusions']=['修订为方案 C']
        second=module.prepare(revised,first)
        self.assertEqual(first['submission_id'],second['submission_id'])
        self.assertNotEqual(first['request_fingerprint'],second['request_fingerprint'])
        self.assertEqual(second['state'],'awaiting_confirmation')

    def test_new_requests_have_unique_ids(self):
        self.assertNotEqual(module.prepare(self.draft())['submission_id'],module.prepare(self.draft())['submission_id'])

    def test_missing_context_and_cancelled_packet_fail_closed(self):
        invalid=self.draft(); invalid.pop('author')
        with self.assertRaises(ValueError):module.prepare(invalid)
        packet=module.prepare(self.draft()); packet['state']='cancelled'
        with self.assertRaises(ValueError):module.prepare(self.draft(),packet)

    def test_exploration_does_not_invent_conclusion(self):
        draft=self.draft();draft['kind']='exploration';draft['conclusions']=[]
        self.assertIn('未形成正式结论',module.prepare(draft)['record_content'])

    def test_attachment_bytes_and_binary_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'result.txt';path.write_bytes(b'line1\r\nline2\r\n')
            draft=self.draft();draft['artifacts']=[{'path':str(path)}]
            packet=module.prepare(draft)
            self.assertEqual(packet['artifact_manifest'][0]['bytes'],14)
            self.assertEqual(packet['files'][1]['content'].encode('utf-8'),path.read_bytes())
            draft['artifacts'][0]['name']='../escape.txt'
            with self.assertRaises(ValueError):module.prepare(draft)
            path.write_bytes(b'a\x00b');draft['artifacts']=[{'path':str(path)}]
            with self.assertRaises(ValueError):module.prepare(draft)

    def test_rejection_never_reports_success(self):
        result=module.evaluate_receipt('rejected','absent')
        self.assertFalse(result['report_success'])
        self.assertEqual(result['state'],'failed')

    def test_unknown_write_requires_remote_read_before_retry(self):
        result=module.evaluate_receipt('unknown','not_checked')
        self.assertEqual(result['action'],'read_remote_before_retry')
        self.assertFalse(result['report_success'])
        found=module.evaluate_receipt('unknown','exact_match')
        self.assertEqual(found['action'],'return_existing_commit_no_write')

    def test_success_response_without_verification_is_not_success(self):
        for remote in ('absent','unreadable','partial_or_different'):
            self.assertFalse(module.evaluate_receipt('success',remote)['report_success'])

    def test_external_link_preserved_without_claiming_access(self):
        draft=self.draft();draft['links']=[{'name':'公开参考','url':'https://example.org/result'}]
        packet=module.prepare(draft)
        self.assertFalse(packet['links'][0]['verified'])
        self.assertIn('未验证访问',packet['record_content'])
        draft['links'][0]['url']='https://example.org/result?token=synthetic'
        with self.assertRaises(ValueError):module.prepare(draft)

    def test_credentials_cannot_enter_record(self):
        draft=self.draft();draft['work']=['gh'+'p_'+'x'*36]
        with self.assertRaises(ValueError):module.prepare(draft)

if __name__=='__main__':unittest.main()
