"""Plan and explicitly confirmed Git upload of one existing Work Sync packet.
No token handling. Never uploads during planning. Git stderr is never exposed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile

LIMIT = 25 * 1024 * 1024
TOTAL_LIMIT = 100 * 1024 * 1024
SECRET = re.compile(rb'github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|Bearer\s+[A-Za-z0-9._-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----')


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def payload(packet):
    sid = packet['submission_id']
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,95}', sid) or packet.get('state') != 'awaiting_confirmation':
        raise ValueError('invalid_or_cancelled_packet')
    base = f'records/{sid}/'
    files = {}
    for item in packet['files']:
        files[item['path']] = item['content'].encode('utf-8')
    for item in packet.get('binary_files', []):
        source = Path(item['source'])
        if source.suffix.lower() not in ('.docx', '.pdf', '.pptx', '.png', '.jpg', '.jpeg', '.gif', '.webp') or PurePosixPath(item['path']).suffix.lower() != source.suffix.lower():
            raise ValueError('unsupported_or_mislabelled_binary')
        if source.is_symlink() or not source.is_file() or source.stat().st_size > LIMIT:
            raise ValueError('source_changed_or_unavailable')
        raw = source.read_bytes()
        if len(raw) != item['bytes'] or hashlib.sha256(raw).hexdigest() != item['sha256']:
            raise ValueError('source_changed_repreview_required')
        if item['path'] in files:
            raise ValueError('duplicate_path')
        files[item['path']] = raw
    if len(files) != len(packet['files']) + len(packet.get('binary_files', [])):
        raise ValueError('duplicate_path')
    if files.get(base + 'record.md') != packet['record_content'].encode('utf-8'):
        raise ValueError('record_mismatch')
    seen = set()
    for name, raw in files.items():
        rel = name[len(base):] if name.startswith(base) else ''
        if rel != 'record.md' and not (rel.startswith('artifacts/') and len(PurePosixPath(rel).parts) == 2):
            raise ValueError('path_outside_record')
        if not rel or any(p in ('.', '..') or not re.fullmatch(r'[\w .()-]+', p) or p.endswith((' ', '.')) for p in PurePosixPath(rel).parts) or '\\' in name:
            raise ValueError('unsafe_path')
        if name.casefold() in seen or len(raw) > LIMIT or SECRET.search(raw):
            raise ValueError('duplicate_oversize_or_credential')
        seen.add(name.casefold())
    manifests = packet.get('artifact_manifest', [])
    if len(manifests) != len(files) - 1 or {base + x['path'] for x in manifests} != set(files) - {base + 'record.md'}:
        raise ValueError('artifact_manifest_mismatch')
    for item in manifests:
        raw = files[base + item['path']]
        if item['bytes'] != len(raw) or item['sha256'] != hashlib.sha256(raw).hexdigest():
            raise ValueError('artifact_manifest_mismatch')
    if sum(map(len, files.values())) > TOTAL_LIMIT:
        raise ValueError('packet_exceeds_100_MiB_limit')
    return files


def plan(packet, repository, branch, member):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository) or any(x in ('.', '..') for x in repository.split('/')):
        raise ValueError('invalid_repository')
    if not re.fullmatch(r'[A-Za-z0-9_./-]+', branch) or branch.startswith(('-', '/')) or '..' in branch or '@{' in branch or branch.endswith(('/', '.', '.lock')) or '//' in branch:
        raise ValueError('invalid_branch')
    authors = re.findall(r'^- 提交成员：(.+)$', packet['record_content'], re.M)
    if authors != [member]:
        raise ValueError('member_does_not_match_packet')
    files = payload(packet)
    binary = {x['path'] for x in packet.get('binary_files', [])}
    if not binary:
        raise ValueError('text_only_use_existing_MCP_flow')
    result = {'version': 1, 'repository': repository, 'branch': branch, 'member': member,
              'submission_id': packet['submission_id'], 'packet': packet,
              'mechanism': 'isolated_git_single_commit',
              'manifest': [{'path': p, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                            'kind': 'binary' if p in binary else 'record' if p.endswith('/record.md') else 'text'}
                           for p, data in files.items()]}
    result['confirmation_sha256'] = digest(result)
    return result


class GitFailure(Exception):
    pass


class Git:
    def __init__(self, directory, env=None):
        self.directory = Path(directory)
        self.env = (os.environ if env is None else env).copy()
        for key in list(self.env):
            if key.startswith('GIT_TRACE') or key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES', 'GIT_NAMESPACE', 'GIT_CONFIG_COUNT', 'GIT_CONFIG_PARAMETERS'):
                self.env.pop(key, None)
        self.env.update(GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='Never')

    def run(self, *args, data=None):
        try:
            r = subprocess.run(['git', '-c', 'core.hooksPath=' + str(self.directory / 'disabled-hooks'), *args],
                               cwd=self.directory, env=self.env, input=data, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, timeout=120)
        except (OSError, subprocess.TimeoutExpired):
            raise GitFailure('git_operation_failed_check_auth_network_or_state') from None
        if r.returncode:
            raise GitFailure('git_operation_failed_check_auth_network_or_state')
        return r.stdout

    def init(self):
        self.run('init', '--quiet', '--template=')

    def tree(self, commit):
        result = {}
        for entry in self.run('ls-tree', '-r', '-z', commit).split(b'\0'):
            if entry:
                metadata, path = entry.split(b'\t', 1)
                mode, kind, oid = metadata.decode('ascii').split()
                result[path.decode('utf-8')] = (mode, kind, oid)
        return result


def remote_files(git, commit, files):
    tree = git.tree(commit)
    report = []
    for name, raw in files.items():
        item = tree.get(name)
        if item is None or item[0] != '100644' or item[1] != 'blob':
            state = 'missing_or_wrong_type'
        else:
            received = git.run('cat-file', 'blob', item[2])
            state = 'verified' if received == raw else 'different'
        report.append({'path': name, 'status': state, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    return report


def stage(git, parent, files, submission_id):
    """Construct one local commit; no network and no working-tree filters/hooks."""
    tree = git.tree(parent)
    prefix = f'records/{submission_id}/'
    existing = {p for p in tree if p.startswith(prefix)}
    for name in files:
        parts = PurePosixPath(name).parts
        if any('/'.join(parts[:i]) in tree for i in range(1, len(parts))):
            raise ValueError('parent_path_conflict')
    if existing:
        checks = remote_files(git, parent, files)
        if existing == set(files) and all(x['status'] == 'verified' for x in checks):
            return None
        raise ValueError('existing_record_conflict_or_partial_stop')
    git.run('read-tree', parent)
    for name, raw in files.items():
        oid = git.run('hash-object', '-w', '--no-filters', '--stdin', data=raw).decode().strip()
        git.run('update-index', '--add', '--cacheinfo', '100644', oid, name)
    tree_oid = git.run('write-tree').decode().strip()
    return git.run('commit-tree', tree_oid, '-p', parent, data=('TeamBrain Work Sync ' + submission_id + '\n').encode()).decode().strip()


def execute(value, confirmation):
    if not isinstance(confirmation, str) or confirmation != value.get('confirmation_sha256') or digest({k: v for k, v in value.items() if k != 'confirmation_sha256'}) != confirmation:
        return {'status': 'confirmation_required', 'remote_write_attempted': False}
    expected = plan(value['packet'], value['repository'], value['branch'], value['member'])
    if expected != value:
        raise ValueError('plan_changed_repreview_required')
    files = payload(value['packet'])  # Byte snapshot bound to the approved manifest.
    url = 'https://github.com/' + value['repository'] + '.git'
    ref = 'refs/heads/' + value['branch']
    commit = None
    attempted = False
    def pending(status):
        return [dict(item, status=status) for item in value['manifest']]
    try:
        with tempfile.TemporaryDirectory(prefix='teambrain-upload-') as td:
            git = Git(td)
            git.init()
            git.run('remote', 'add', 'origin', url)
            # Fetch must succeed: no empty repo initialization or auto-created branch here.
            git.run('fetch', '--quiet', '--depth=1', 'origin', ref)
            parent = git.run('rev-parse', 'FETCH_HEAD').decode().strip()
            # Reuse existing Git identity, never invent or write global config.
            for key in ('user.name', 'user.email'):
                identity = git.run('config', '--get', key).decode('utf-8').strip()
                if not identity:
                    raise GitFailure('existing_git_commit_identity_required')
            commit = stage(git, parent, files, value['submission_id'])
            if commit is None:
                checks = remote_files(git, parent, files)
                kinds = {x['path']: x['kind'] for x in value['manifest']}
                for item in checks:
                    item['kind'] = kinds[item['path']]
                return {'status': 'already_present_verified', 'commit': parent, 'files': checks, 'remote_write_attempted': False}
            latest = git.run('ls-remote', 'origin', ref).split()
            if not latest or latest[0].decode() != parent:
                return {'status': 'branch_changed_stop', 'remote_write_attempted': False, 'files': pending('not_uploaded')}
            attempted = True
            try:
                git.run('push', '--quiet', 'origin', commit + ':' + ref)  # Never force.
            except GitFailure:
                pass  # Unknown response: inspect the remote, never retry the push.
            with tempfile.TemporaryDirectory(prefix='teambrain-verify-') as vd:
                verify = Git(vd)
                verify.init()
                verify.run('fetch', '--quiet', '--depth=1', url, ref)
                actual = verify.run('rev-parse', 'FETCH_HEAD').decode().strip()
                if actual != commit:
                    return {'status': 'outcome_unknown_check_remote_no_retry', 'candidate_commit': commit, 'remote_write_attempted': True, 'files': pending('unknown')}
                checks = remote_files(verify, actual, files)
                kinds = {x['path']: x['kind'] for x in value['manifest']}
                for item in checks:
                    item['kind'] = kinds[item['path']]
                return {'status': 'verified' if all(x['status'] == 'verified' for x in checks) else 'partial_or_different_stop',
                        'commit': actual, 'url': 'https://github.com/' + value['repository'] + '/commit/' + actual,
                        'files': checks, 'remote_write_attempted': True}
    except GitFailure:
        return {'status': 'outcome_unknown_check_remote_no_retry' if attempted else 'git_unavailable_auth_network_identity_or_branch_error',
                'candidate_commit': commit, 'remote_write_attempted': attempted, 'files': pending('unknown' if attempted else 'not_uploaded')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('plan')
    p.add_argument('--packet', required=True)
    p.add_argument('--repository', required=True)
    p.add_argument('--branch', required=True)
    p.add_argument('--member', required=True)
    p.add_argument('--output', required=True)
    p = sub.add_parser('upload')
    p.add_argument('--plan', required=True)
    p.add_argument('--confirm', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'plan':
            value = plan(json.loads(Path(args.packet).read_text(encoding='utf-8')), args.repository, args.branch, args.member)
            output = Path(args.output)
            if output.exists():
                raise ValueError('plan_output_exists_choose_new_path')
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
            result = {k: v for k, v in value.items() if k != 'packet'}
            result['status'] = 'awaiting_human_confirmation'
        else:
            result = execute(json.loads(Path(args.plan).read_text(encoding='utf-8')), args.confirm)
    except (ValueError, KeyError, TypeError, OSError):
        result = {'status': 'invalid_changed_or_unreadable_input_stop', 'success': False}
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
