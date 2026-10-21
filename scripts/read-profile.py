"""Read only the confirmed, non-secret fields of a local TeamBrain profile."""
import json
import os
from pathlib import Path
import re


def profile_path():
    # USERPROFILE is the interactive user's home inherited by native Windows Codex.
    home = Path(os.environ['USERPROFILE']) if os.name == 'nt' else Path.home()
    return home / '.config' / 'teambrain' / 'profile.json'


def read_profile(path=None):
    path = profile_path() if path is None else Path(path)
    try:
        raw = path.read_text(encoding='utf-8-sig')
    except FileNotFoundError:
        return {'status': 'not_found'}
    except PermissionError:
        return {'status': 'access_denied'}
    except (OSError, UnicodeError):
        return {'status': 'read_error'}
    try:
        data = json.loads(raw)
        if not isinstance(data, dict) or data.get('version') != 1:
            return {'status': 'unsupported_schema'}
        key = data.get('active_project')
        if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', key):
            return {'status': 'unbound'}
        project = data.get('projects', {}).get(key)
        if not isinstance(project, dict) or project.get('repository_confirmed') is not True:
            return {'status': 'unbound'}
        branch = project.get('branch')
        if not isinstance(branch, str) or not branch.strip():
            return {'status': 'invalid_profile'}
        member = project.get('member', {})
        member = member if isinstance(member, dict) else {}
        result = {'status': 'ok', 'repository': key, 'branch': branch, 'repository_confirmed': True}
        if member.get('confirmed') is True and isinstance(member.get('display_name'), str) and member['display_name'].strip():
            result['member'] = {'display_name': member['display_name'], 'confirmed': True}
        connection = project.get('preferred_connection')
        if isinstance(connection, str) and re.fullmatch(r'[A-Za-z0-9_-]+', connection):
            result['preferred_connection'] = connection
        return result
    except (ValueError, TypeError, AttributeError):
        return {'status': 'invalid_profile'}


if __name__ == '__main__':
    print(json.dumps(read_profile(), ensure_ascii=False, indent=2))
