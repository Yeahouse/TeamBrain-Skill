"""Prepare a local, unconfirmed text synchronization packet; no network access."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import uuid
from urllib.parse import urlsplit, parse_qs


def evaluate_receipt(write_outcome, remote_state):
    """Classify observed outcomes without issuing or retrying any network call."""
    if write_outcome not in ('success', 'rejected', 'unknown'):
        raise ValueError('Invalid write outcome')
    if remote_state not in ('not_checked', 'unreadable', 'absent', 'exact_match', 'partial_or_different'):
        raise ValueError('Invalid remote state')
    if remote_state == 'exact_match':
        return {'state': 'verified', 'report_success': True, 'action': 'return_existing_commit_no_write'}
    if remote_state == 'partial_or_different':
        return {'state': 'conflict_or_partial', 'report_success': False, 'action': 'stop_and_preview_repair'}
    if remote_state in ('not_checked', 'unreadable'):
        return {'state': 'outcome_unknown', 'report_success': False, 'action': 'read_remote_before_retry'}
    if write_outcome == 'rejected':
        return {'state': 'failed', 'report_success': False, 'action': 'report_failure_no_retry'}
    if write_outcome == 'success':
        return {'state': 'verification_failed', 'report_success': False, 'action': 'inspect_remote_no_retry'}
    return {'state': 'retry_confirmation_required', 'report_success': False, 'action': 'keep_id_and_ask_before_retry'}


def prepare(draft, previous=None):
    required = ('request_key', 'author', 'stage', 'topic', 'kind', 'work')
    allowed = set(required) | {'discussion', 'conclusions', 'open_questions', 'artifacts', 'links', 'submission_id', 'occurred_at'}
    if set(draft) - allowed:
        raise ValueError('Unknown fields; do not pass raw conversation or credentials')
    for key in required:
        if not draft.get(key):
            raise ValueError(f'Missing {key}; ask the user rather than inventing it')
    if draft['kind'] not in ('decision', 'exploration'):
        raise ValueError('kind must be decision or exploration')
    for key in ('request_key', 'author', 'stage', 'topic'):
        if not isinstance(draft[key], str) or '\n' in draft[key] or '\r' in draft[key]:
            raise ValueError(f'{key} must be a single-line string')
    for key in ('work', 'discussion', 'conclusions', 'open_questions'):
        values = draft.get(key, [])
        if not isinstance(values, list) or any(not isinstance(x, str) or not x.strip() for x in values):
            raise ValueError(f'{key} must be a list of nonempty strings')
    if draft['kind'] == 'decision' and not draft.get('conclusions'):
        raise ValueError('No formal conclusion supplied; use exploration or ask the user')
    if previous and previous['request_key'] != draft['request_key']:
        raise ValueError('Output belongs to another request; choose a new output path')
    if previous and previous.get('state') == 'cancelled':
        raise ValueError('Cancelled request must not be silently resumed')
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
    submission_id = draft.get('submission_id') or (previous or {}).get('submission_id') or 'ws-' + uuid.uuid4().hex
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,95}', submission_id):
        raise ValueError('Invalid submission_id')
    if previous and previous['submission_id'] != submission_id:
        raise ValueError('A request must keep its existing ID')
    created_at = (previous or {}).get('created_at', now)
    base = f'records/{submission_id}'
    files, artifacts, names = [], [], set()
    for item in draft.get('artifacts', []):
        source = Path(item['path'])
        name = item.get('name') or source.name
        if name in ('.', '..') or '/' in name or '\\' in name or ':' in name or name.casefold() in names:
            raise ValueError('Unsafe or duplicate attachment name')
        names.add(name.casefold())
        if source.suffix.lower() not in ('.md', '.markdown', '.txt') or Path(name).suffix.lower() not in ('.md', '.markdown', '.txt'):
            raise ValueError('Unsupported artifact type; list as not uploaded instead')
        data = source.read_bytes()
        content = data.decode('utf-8')
        if '\x00' in content:
            raise ValueError('Binary content cannot use text synchronization')
        target = f'{base}/artifacts/{name}'
        files.append({'path': target, 'content': content})
        artifacts.append({'path': f'artifacts/{name}', 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    links = []
    for item in draft.get('links', []):
        url = item['url']
        parsed = urlsplit(url)
        if parsed.scheme not in ('https', 'http') or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError('Provide a shareable HTTP(S) link without embedded credentials')
        if any(k.lower() in ('token', 'access_token', 'auth', 'key', 'api_key', 'signature', 'sig') for k in parse_qs(parsed.query)):
            raise ValueError('Credential-bearing temporary links cannot be published')
        links.append({'name': item['name'], 'url': url, 'verified': bool(item.get('verified', False))})
    def section(title, values, fallback):
        return '\n## ' + title + '\n\n' + ('\n'.join('- ' + x for x in values) if values else fallback) + '\n'
    record = f"# {draft['topic']}\n\n- 记录 ID：{submission_id}\n- 提交成员：{draft['author']}\n- 工作时间：{draft.get('occurred_at') or '未提供'}\n- 草稿生成时间：{created_at}\n- 项目阶段：{draft['stage']}\n- 记录类型：{'阶段结论' if draft['kind']=='decision' else '探索记录'}\n- 确认方式：本预览须经用户明确确认后才可提交\n- 同步核验：提交前内容快照，实际结果另记运行回执\n"
    record += section('主要工作', draft['work'], '未提供')
    record += section('讨论过程与方案取舍', draft.get('discussion', []), '无额外讨论信息')
    record += section('阶段结论', draft.get('conclusions', []), '未形成正式结论；仅保存探索过程，不作为正式决定。')
    record += section('关联成果', [f"{a['path']}；{a['bytes']} 字节；SHA-256 {a['sha256']}" for a in artifacts], '无拟上传文本成果')
    record += section('外部成果链接', [f"{x['name']}：{x['url']}（{'已核对访问' if x['verified'] else '未验证访问'}）" for x in links], '无')
    record += section('待解决问题', draft.get('open_questions', []), '未提供其他未决问题')
    files.insert(0, {'path': f'{base}/record.md', 'content': record})
    secret_pattern = re.compile(r'(?:github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|Bearer\s+[A-Za-z0-9_.-]{20,})')
    if any(secret_pattern.search(item['content']) for item in files):
        raise ValueError('Potential credential found in proposed content; exclude it before preview')
    digest = hashlib.sha256(json.dumps(files, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
    return {'request_key': draft['request_key'], 'submission_id': submission_id, 'created_at': created_at, 'state': 'awaiting_confirmation', 'request_fingerprint': digest, 'record_content': record, 'files': files, 'artifact_manifest': artifacts, 'links': links}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = Path(args.output)
    draft = json.loads(Path(args.input).read_text(encoding='utf-8'))
    previous = json.loads(output.read_text(encoding='utf-8')) if output.exists() else None
    packet = prepare(draft, previous)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(packet, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'submission_id': packet['submission_id'], 'state': packet['state'], 'files': [x['path'] for x in packet['files']]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
