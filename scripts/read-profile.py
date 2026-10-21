"""TeamBrain local project profiles: inspect, resolve, preview, and confirmed save.

No network access; no credential storage. CLI confirmation binds an exact preview,
but the calling AI must separately obtain the human's approval.
"""
import argparse
import copy
import ctypes
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from urllib.parse import urlsplit
import uuid


def profile_path():
    home = Path(os.environ['USERPROFILE']) if os.name == 'nt' else Path.home()
    return home / '.config' / 'teambrain' / 'profile.json'


def _path(path):
    return profile_path() if path is None else Path(path)


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def repository_id(value):
    value = value.strip().strip('「」“”\"\'<>')
    if '://' in value:
        url = urlsplit(value)
        if url.scheme != 'https' or url.netloc.lower() != 'github.com' or url.query or url.fragment:
            raise ValueError('invalid_repository')
        value = url.path.strip('/')
    value = value.removesuffix('.git')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', value):
        raise ValueError('invalid_repository')
    if any(p in ('.', '..') or p.endswith('.lock') for p in value.split('/')):
        raise ValueError('invalid_repository')
    return value


def _safe(value):
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = re.sub(r'[^a-z]', '', str(key).lower())
            if normalized in ('token','accesstoken','refreshtoken','authorization','password','apikey','privatekey','clientsecret'):
                return False
            if not _safe(item):
                return False
    elif isinstance(value, list):
        return all(_safe(item) for item in value)
    elif isinstance(value, str):
        if re.search(r'github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|Bearer\s+\S{20,}|-----BEGIN .*PRIVATE KEY-----|[?&](?:token|access_token)=', value, re.I):
            return False
    return True


def _load(path):
    try:
        text = path.read_text(encoding='utf-8-sig')
    except FileNotFoundError:
        return {'status': 'not_found'}
    except PermissionError:
        return {'status': 'access_denied'}
    except (OSError, UnicodeError):
        return {'status': 'read_error'}
    try:
        data = json.loads(text)
        if not isinstance(data, dict) or type(data.get('version')) is not int or data['version'] != 1:
            return {'status': 'unsupported_schema'}
        projects = data.get('projects', {})
        if not isinstance(projects, dict):
            return {'status': 'invalid_profile'}
        seen = set()
        for key, project in projects.items():
            if repository_id(key) != key or key.casefold() in seen or not isinstance(project, dict):
                return {'status': 'invalid_profile'}
            seen.add(key.casefold())
        if not _safe(data):
            return {'status': 'sensitive_config'}
        return {'status': 'ok', 'data': data}
    except (ValueError, TypeError, AttributeError):
        return {'status': 'invalid_profile'}


def _view(key, project):
    result = {'repository': key, 'name': project.get('name') if isinstance(project.get('name'),str) else key,
              'branch': project.get('branch'), 'repository_confirmed': project.get('repository_confirmed') is True,
              'remote_access': 'not_verified_this_session'}
    member = project.get('member')
    if isinstance(member, dict) and member.get('confirmed') is True and isinstance(member.get('display_name'), str) and member['display_name'].strip():
        result['member'] = {'display_name': member['display_name'], 'confirmed': True}
        if isinstance(member.get('role'), str):
            result['member']['role'] = member['role']
    connection = project.get('preferred_connection')
    if isinstance(connection,str) and re.fullmatch(r'[A-Za-z0-9_-]+', connection):
        result['preferred_connection'] = connection
    return result


def list_profile(path=None):
    loaded = _load(_path(path))
    if loaded['status'] != 'ok':
        return loaded
    data = loaded['data']
    projects = [_view(k, p) for k, p in data.get('projects',{}).items()]
    return {'status': 'ok' if projects else 'empty', 'projects': projects,
            'saved_active_project': data.get('active_project'), 'session_target_confirmed': False}


def read_profile(path=None):
    """Backward-compatible active-candidate view; never authorizes a session target."""
    loaded = _load(_path(path))
    if loaded['status'] != 'ok':
        return loaded
    data = loaded['data']
    key = data.get('active_project')
    project = data.get('projects',{}).get(key) if isinstance(key,str) else None
    if not isinstance(project,dict) or project.get('repository_confirmed') is not True:
        return {'status': 'unbound'}
    if not isinstance(project.get('branch'),str) or not project['branch'].strip():
        return {'status': 'invalid_profile'}
    result = _view(key,project)
    result['status'] = 'ok'
    return result


def _select(data, selector):
    projects = data.get('projects',{})
    try:
        key = repository_id(selector)
    except (ValueError,AttributeError):
        matches = [k for k,p in projects.items() if isinstance(p.get('name'),str) and p['name'].casefold()==str(selector).casefold()]
    else:
        matches = [k for k in projects if k.casefold()==key.casefold()]
        if not matches:
            return {'status': 'not_bound', 'repository': key}
    if len(matches)>1:
        return {'status':'ambiguous_project','candidates':[_view(k,projects[k]) for k in matches]}
    if not matches:
        return {'status':'project_not_found'}
    return {'status':'ok','repository':matches[0]}


def resolve_target(path=None, explicit=None, session=None, use_saved=False, branch=None, require_member=False):
    loaded = _load(_path(path))
    if loaded['status']=='not_found':
        data={'version':1,'projects':{}}
    elif loaded['status']!='ok':
        return loaded
    else:
        data=loaded['data']
    selector = explicit if explicit is not None else session if session is not None else (data.get('active_project') if use_saved else None)
    if selector is not None and (not isinstance(selector,str) or not selector.strip()):
        return {'status':'invalid_target'}
    if not selector:
        return {'status':'needs_target_confirmation' if data.get('projects') else 'no_projects',
                'projects':[_view(k,p) for k,p in data.get('projects',{}).items()],
                'saved_active_project':data.get('active_project')}
    selected=_select(data,selector)
    if selected['status']=='not_bound':
        return {'status':'target_unbound','repository':selected['repository'],'branch':branch,
                'remote_access':'not_verified_this_session','reason':'explicit' if explicit is not None else 'session'}
    if selected['status']!='ok':
        return selected
    key=selected['repository']; project=data['projects'][key]
    if project.get('repository_confirmed') is not True:
        return {'status':'binding_unconfirmed','repository':key}
    result=_view(key,project)
    result.update(status='ok',reason='explicit' if explicit is not None else 'session' if session is not None else 'explicit_saved_default')
    if branch is not None:
        result['branch']=branch
    if not isinstance(result['branch'],str) or not result['branch'].strip():
        result['status']='branch_required'
    elif require_member and 'member' not in result:
        result['status']='member_required'
    return result


def _text(value, required=True):
    if not isinstance(value,str) or (required and not value.strip()) or any(ord(c)<32 for c in value) or not _safe(value):
        raise ValueError('invalid_field')
    return value.strip()


def _branch(value):
    value=_text(value)
    if re.search(r'[\s~^:?*\[\\]|\.\.|//|@\{',value) or value.startswith('/') or value.endswith(('/', '.', '.lock')):
        raise ValueError('invalid_branch')
    return value


def _plan_hash(plan):
    return _digest(json.dumps({k:v for k,v in plan.items() if k!='confirmation_sha256'},ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8'))


def prepare_change(operation, path=None, selector=None, name=None, branch='main', member=None, role=None, connection=None):
    path=_path(path);loaded=_load(path)
    if loaded['status']=='not_found' and operation=='add':
        data={'version':1,'projects':{}}
    elif loaded['status']!='ok':
        return loaded
    else:
        data=loaded['data']
    try:
        if operation=='add':
            key=repository_id(selector); selected=_select(data,key)
            if selected['status']=='ok':
                return {'status':'already_bound','project':_view(selected['repository'],data['projects'][selected['repository']])}
            if name is None:
                return {'status':'project_name_required','repository':key}
            changes={'name':_text(name),'branch':_branch(branch),'repository_confirmed':True}
            if member is not None:
                changes['member']={'display_name':_text(member),'confirmed':True}
                if role is not None:changes['member']['role']=_text(role,False)
            elif role is not None:
                return {'status':'member_required'}
            if connection is not None:
                if not re.fullmatch(r'[A-Za-z0-9_-]+',connection):raise ValueError('invalid_connection')
                changes['preferred_connection']=connection
            before=None;after=_view(key,changes)
        elif operation in ('switch','member'):
            selected=_select(data,selector)
            if selected['status']!='ok':return selected
            key=selected['repository'];before=_view(key,data['projects'][key])
            if operation=='switch':
                changes={'active_project':key};after=before.copy()
            else:
                updated=copy.deepcopy(data['projects'][key]);m=updated.get('member',{})
                m=m.copy() if isinstance(m,dict) else {}
                m.update(display_name=_text(member),confirmed=True)
                if role is not None:m['role']=_text(role,False)
                changes={'member':m};updated.update(changes);after=_view(key,updated)
        else:
            return {'status':'invalid_operation'}
        raw=path.read_bytes() if loaded['status']=='ok' else None
        plan={'status':'preview','version':1,'operation':operation,'repository':key,'changes':changes,
              'base_sha256':_digest(raw) if raw is not None else 'missing',
              'profile_id':_digest(str(path.resolve()).casefold().encode('utf-8')),
              'before':before,'after':after,'saved_active_before':data.get('active_project')}
        plan['confirmation_sha256']=_plan_hash(plan)
        return plan
    except PermissionError:return {'status':'access_denied'}
    except OSError:return {'status':'read_error'}
    except (ValueError,TypeError,AttributeError):return {'status':'invalid_input'}


def _copy_permissions(source,target):
    if os.name!='nt':
        os.chmod(target,stat.S_IMODE(source.stat().st_mode));return
    adv=ctypes.WinDLL('advapi32',use_last_error=True)
    get=adv.GetFileSecurityW; get.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.POINTER(ctypes.c_uint32)]
    put=adv.SetFileSecurityW; put.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_void_p]
    size=ctypes.c_uint32();get(str(source),4,None,0,ctypes.byref(size))
    if not size.value:raise PermissionError('Cannot retain local security descriptor')
    buffer=ctypes.create_string_buffer(size.value)
    control=ctypes.c_ushort();revision=ctypes.c_uint32()
    if not get(str(source),4,buffer,size.value,ctypes.byref(size)):
        raise PermissionError('Cannot retain local security descriptor')
    if not adv.GetSecurityDescriptorControl(buffer,ctypes.byref(control),ctypes.byref(revision)):
        raise PermissionError('Cannot inspect local security descriptor')
    flags=4 | (0x80000000 if control.value & 0x1000 else 0x20000000)
    if not put(str(target),flags,buffer):
        raise PermissionError('Cannot retain local security descriptor')


def apply_change(plan, confirmation, path=None):
    path=_path(path)
    if not isinstance(plan,dict) or plan.get('status')!='preview' or plan.get('version')!=1 or not _safe(plan):
        return {'status':'invalid_plan'}
    digest=_plan_hash(plan)
    if not isinstance(confirmation,str) or not hmac.compare_digest(digest,confirmation) or digest!=plan.get('confirmation_sha256'):
        return {'status':'confirmation_required'}
    if plan.get('profile_id')!=_digest(str(path.resolve()).casefold().encode('utf-8')):
        return {'status':'profile_mismatch'}
    lock=None;temporary=None;backup=None
    try:
        path.parent.mkdir(parents=True,exist_ok=True)
        lock=path.with_name(path.name+'.teambrain.lock')
        try:fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        except FileExistsError:return {'status':'profile_busy'}
        os.close(fd)
        loaded=_load(path)
        if loaded['status']=='not_found':
            raw=None;data={'version':1,'projects':{}}
        elif loaded['status']!='ok':
            return loaded
        else:
            raw=path.read_bytes();data=loaded['data']
        if (_digest(raw) if raw is not None else 'missing')!=plan.get('base_sha256'):
            return {'status':'profile_changed_repreview_required'}
        new=copy.deepcopy(data);projects=new.setdefault('projects',{});key=repository_id(plan['repository'])
        operation=plan['operation'];changes=plan['changes']
        if operation=='add':
            if any(k.casefold()==key.casefold() for k in projects):return {'status':'already_bound'}
            # Revalidate the exact additive operation rather than trusting an edited plan.
            m=changes.get('member',{})
            expected=prepare_change('add',path,key,changes.get('name'),changes.get('branch'),m.get('display_name'),m.get('role'),changes.get('preferred_connection'))
            if expected.get('changes')!=changes:return {'status':'invalid_plan'}
            projects[key]=copy.deepcopy(changes)
            if not new.get('active_project'):new['active_project']=key
        elif operation=='switch':
            if key not in projects or changes!={'active_project':key}:return {'status':'invalid_plan'}
            new['active_project']=key
        elif operation=='member':
            if key not in projects:return {'status':'project_not_found'}
            m=changes.get('member',{})
            expected=prepare_change('member',path,key,member=m.get('display_name'),role=m.get('role'))
            if expected.get('changes')!=changes:return {'status':'invalid_plan'}
            projects[key]['member']=copy.deepcopy(m)
        else:return {'status':'invalid_plan'}
        payload=(json.dumps(new,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
        if raw is not None:
            backup=path.with_name(path.name+'.'+uuid.uuid4().hex+'.bak')
            fd=os.open(backup,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
            _copy_permissions(path,backup)
            if _digest(backup.read_bytes())!=plan['base_sha256']:raise OSError('Backup verification failed')
        fd,temp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent);temporary=Path(temp)
        with os.fdopen(fd,'wb') as f:f.write(payload);f.flush();os.fsync(f.fileno())
        if raw is not None:_copy_permissions(path,temporary)
        if json.loads(temporary.read_text(encoding='utf-8'))!=new:raise OSError('Temporary data verification failed')
        # Stop if a manual edit occurred after the preview/base check.
        current=path.read_bytes() if raw is not None else None
        if raw is None and path.exists():return {'status':'profile_changed_repreview_required'}
        if current!=raw:return {'status':'profile_changed_repreview_required'}
        os.replace(temporary,path);temporary=None
        if path.read_bytes()!=payload:raise OSError('Saved data verification failed')
        return {'status':'saved','operation':operation,'project':_view(key,projects[key]),'saved_active_project':new.get('active_project'),
                'backup_created':backup is not None,'backup_sha256':_digest(raw) if raw is not None else None,
                'profile_sha256':_digest(payload),'remote_access':'not_verified_this_session'}
    except PermissionError:return {'status':'access_denied'}
    except (ValueError,TypeError,KeyError,AttributeError):return {'status':'invalid_plan'}
    except OSError:return {'status':'write_error_check_local_state'}
    finally:
        if temporary is not None:
            try:temporary.unlink()
            except OSError:pass
        if lock is not None:
            # Only remove a lock actually created by this invocation.
            if 'fd' in locals():
                try:lock.unlink()
                except OSError:pass


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',help='Explicit alternate local profile, e.g. an isolated test fixture; does not change the default')
    sub=parser.add_subparsers(dest='command')
    sub.add_parser('list')
    resolve=sub.add_parser('resolve');resolve.add_argument('--explicit');resolve.add_argument('--session');resolve.add_argument('--use-saved',action='store_true');resolve.add_argument('--branch');resolve.add_argument('--require-member',action='store_true')
    preview=sub.add_parser('preview');preview.add_argument('operation',choices=['add','switch','member']);preview.add_argument('--project',required=True);preview.add_argument('--name');preview.add_argument('--branch',default='main');preview.add_argument('--member');preview.add_argument('--role');preview.add_argument('--connection')
    apply=sub.add_parser('apply');apply.add_argument('--plan',required=True);apply.add_argument('--confirm',required=True)
    args=parser.parse_args()
    if args.command=='list':result=list_profile(args.profile)
    elif args.command=='resolve':result=resolve_target(args.profile,args.explicit,args.session,args.use_saved,args.branch,args.require_member)
    elif args.command=='preview':result=prepare_change(args.operation,args.profile,args.project,args.name,args.branch,args.member,args.role,args.connection)
    elif args.command=='apply':
        try:result=apply_change(json.loads(Path(args.plan).read_text(encoding='utf-8-sig')),args.confirm,args.profile)
        except PermissionError:result={'status':'access_denied'}
        except (OSError,ValueError):result={'status':'invalid_plan'}
    else:result=read_profile(args.profile)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
