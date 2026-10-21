import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('project_profiles',Path(__file__).parents[1]/'scripts/read-profile.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)


class MultiProjectTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'profile.json'

    def add(self,repo='example/alpha',name='项目甲',member='甲署名'):
        plan=p.prepare_change('add',self.path,repo,name=name,member=member)
        self.assertEqual(plan['status'],'preview')
        result=p.apply_change(plan,plan['confirmation_sha256'],self.path)
        self.assertEqual(result['status'],'saved',result)
        return result

    def test_first_preview_creates_nothing(self):
        plan=p.prepare_change('add',self.path,'example/alpha',name='项目甲')
        self.assertEqual(plan['status'],'preview');self.assertFalse(self.path.exists())
        self.assertEqual(plan['after']['remote_access'],'not_verified_this_session')

    def test_first_add_and_reopen(self):
        self.add()
        result=p.list_profile(self.path)
        self.assertEqual(result['projects'][0]['member']['display_name'],'甲署名')
        self.assertFalse(result['session_target_confirmed'])

    def test_adding_second_preserves_legacy_unknown_data(self):
        self.add();data=json.loads(self.path.read_text(encoding='utf-8'))
        data['extra']={'keep':[1,2]};data['projects']['example/alpha']['custom']='unchanged'
        self.path.write_text(json.dumps(data),encoding='utf-8');old=self.path.read_bytes()
        result=self.add('example/beta','项目乙','乙署名')
        new=json.loads(self.path.read_text(encoding='utf-8'))
        self.assertEqual(new['projects']['example/alpha'],data['projects']['example/alpha'])
        self.assertEqual(new['extra'],data['extra']);self.assertEqual(new['active_project'],'example/alpha')
        self.assertTrue(result['backup_created']);self.assertIn(old,[f.read_bytes() for f in self.path.parent.glob('*.bak')])

    def test_switch_keeps_both_projects_and_members(self):
        self.add();self.add('example/beta','项目乙','乙署名')
        plan=p.prepare_change('switch',self.path,'项目乙')
        self.assertEqual(p.apply_change(plan,plan['confirmation_sha256'],self.path)['status'],'saved')
        data=p.list_profile(self.path);self.assertEqual(len(data['projects']),2)
        self.assertEqual(data['saved_active_project'],'example/beta')
        self.assertEqual(p.resolve_target(self.path,session='example/alpha')['member']['display_name'],'甲署名')
        self.assertEqual(p.resolve_target(self.path,session='example/beta')['member']['display_name'],'乙署名')

    def test_one_or_many_historical_projects_require_confirmation(self):
        self.add();self.assertEqual(p.resolve_target(self.path)['status'],'needs_target_confirmation')
        self.add('example/beta','项目乙','乙署名')
        self.assertEqual(p.resolve_target(self.path)['status'],'needs_target_confirmation')

    def test_explicit_overrides_session_without_saving(self):
        self.add();self.add('example/beta','项目乙','乙署名');old=self.path.read_bytes()
        r=p.resolve_target(self.path,explicit='项目乙',session='example/alpha')
        self.assertEqual(r['repository'],'example/beta');self.assertEqual(r['reason'],'explicit')
        self.assertEqual(self.path.read_bytes(),old)

    def test_explicit_unbound_repository_does_not_inherit_old_member(self):
        self.add();r=p.resolve_target(self.path,explicit='https://github.com/example/beta.git')
        self.assertEqual(r['status'],'target_unbound');self.assertNotIn('member',r)

    def test_empty_explicit_target_never_falls_back_to_session(self):
        self.add()
        self.assertEqual(p.resolve_target(self.path,explicit='',session='example/alpha')['status'],'invalid_target')

    def test_duplicate_repository_case_does_not_overwrite(self):
        self.add();old=self.path.read_bytes()
        self.assertEqual(p.prepare_change('add',self.path,'EXAMPLE/Alpha',name='覆盖')['status'],'already_bound')
        self.assertEqual(self.path.read_bytes(),old)

    def test_same_name_requires_repository_disambiguation(self):
        self.add(name='同名');self.add('example/beta','同名','乙')
        self.assertEqual(p.resolve_target(self.path,explicit='同名')['status'],'ambiguous_project')
        self.assertEqual(p.resolve_target(self.path,explicit='example/beta')['status'],'ok')

    def test_member_change_requires_confirmation_and_is_scoped(self):
        self.add();self.add('example/beta','项目乙','乙署名');old=self.path.read_bytes()
        plan=p.prepare_change('member',self.path,'example/alpha',member='新署名',role='研究')
        self.assertEqual(self.path.read_bytes(),old)
        self.assertEqual(p.apply_change(plan,'incorrect',self.path)['status'],'confirmation_required')
        self.assertEqual(self.path.read_bytes(),old)
        self.assertEqual(p.apply_change(plan,plan['confirmation_sha256'],self.path)['status'],'saved')
        self.assertEqual(p.resolve_target(self.path,session='example/beta')['member']['display_name'],'乙署名')

    def test_stale_preview_does_not_overwrite(self):
        self.add();plan=p.prepare_change('member',self.path,'example/alpha',member='新')
        data=json.loads(self.path.read_text(encoding='utf-8'));data['note']='manual edit'
        self.path.write_text(json.dumps(data),encoding='utf-8');old=self.path.read_bytes()
        self.assertEqual(p.apply_change(plan,plan['confirmation_sha256'],self.path)['status'],'profile_changed_repreview_required')
        self.assertEqual(self.path.read_bytes(),old)

    def test_plan_cannot_be_applied_to_other_profile(self):
        plan=p.prepare_change('add',self.path,'example/alpha',name='甲')
        result=p.apply_change(plan,plan['confirmation_sha256'],Path(self.tmp.name)/'other.json')
        self.assertEqual(result['status'],'profile_mismatch')

    def test_busy_lock_not_removed(self):
        plan=p.prepare_change('add',self.path,'example/alpha',name='甲')
        lock=self.path.with_name(self.path.name+'.teambrain.lock');lock.touch()
        self.assertEqual(p.apply_change(plan,plan['confirmation_sha256'],self.path)['status'],'profile_busy')
        self.assertTrue(lock.exists());self.assertFalse(self.path.exists())

    def test_corrupt_profile_unchanged(self):
        self.path.write_text('{broken',encoding='utf-8');old=self.path.read_bytes()
        self.assertEqual(p.prepare_change('add',self.path,'example/alpha',name='甲')['status'],'invalid_profile')
        self.assertEqual(self.path.read_bytes(),old);self.assertFalse(list(self.path.parent.glob('*.bak')))

    def test_permission_error_is_not_absence(self):
        with patch.object(Path,'read_text',side_effect=PermissionError()):
            self.assertEqual(p.list_profile(self.path),{'status':'access_denied'})
            self.assertEqual(p.prepare_change('add',self.path,'example/alpha',name='甲'),{'status':'access_denied'})

    def test_credentials_rejected_without_output_or_write(self):
        data={'version':1,'projects':{},'token':'secret-placeholder'}
        self.path.write_text(json.dumps(data),encoding='utf-8')
        r=p.list_profile(self.path);self.assertEqual(r,{'status':'sensitive_config'})
        self.assertNotIn('secret-placeholder',json.dumps(r))

    def test_unconfirmed_member_blocks_sync_not_query(self):
        plan=p.prepare_change('add',self.path,'example/alpha',name='甲')
        self.assertEqual(p.apply_change(plan,plan['confirmation_sha256'],self.path)['status'],'saved')
        self.assertEqual(p.resolve_target(self.path,explicit='example/alpha')['status'],'ok')
        self.assertEqual(p.resolve_target(self.path,explicit='example/alpha',require_member=True)['status'],'member_required')

    def test_replace_failure_retains_original(self):
        self.add();plan=p.prepare_change('member',self.path,'example/alpha',member='新');old=self.path.read_bytes()
        with patch.object(p.os,'replace',side_effect=OSError('controlled failure')):
            self.assertEqual(p.apply_change(plan,plan['confirmation_sha256'],self.path)['status'],'write_error_check_local_state')
        self.assertEqual(self.path.read_bytes(),old)

    def test_url_validation(self):
        self.assertEqual(p.repository_id('https://github.com/example/alpha.git'),'example/alpha')
        for url in ['https://other.invalid/example/alpha','https://github.com/example/alpha?token=x','https://github.com/example','example/../alpha']:
            with self.assertRaises(ValueError):p.repository_id(url)

    def test_no_migration_of_legacy_schema(self):
        data={'version':1,'active_project':'example/alpha','projects':{'example/alpha':{'branch':'main','repository_confirmed':True,'member':{'display_name':'旧署名','confirmed':True}}}}
        self.path.write_text(json.dumps(data),encoding='utf-8');old=self.path.read_bytes()
        self.assertEqual(p.list_profile(self.path)['projects'][0]['name'],'example/alpha')
        self.assertEqual(p.read_profile(self.path)['member']['display_name'],'旧署名')
        self.assertEqual(self.path.read_bytes(),old)


if __name__=='__main__':unittest.main()
