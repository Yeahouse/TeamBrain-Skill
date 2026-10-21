# Onboarding 与个人配置复用修复：完整拟提交清单

状态：未暂存、未提交、未推送，等待用户审核。此清单包括上一轮未提交的Onboarding基础功能及本轮最小修复。

共 53 个文件；其中核心实现、说明与日志9个，报告与脱敏证据44个。

- `README.md`
- `SKILL.md`
- `docs/poc-log.md`
- `docs/poc/onboarding-setup/01-intro-answer.md`
- `docs/poc/onboarding-setup/01-intro-events.jsonl`
- `docs/poc/onboarding-setup/01-intro-stderr.txt`
- `docs/poc/onboarding-setup/02-configured-answer.md`
- `docs/poc/onboarding-setup/02-configured-events.jsonl`
- `docs/poc/onboarding-setup/02-configured-stderr.txt`
- `docs/poc/onboarding-setup/03-unbound-answer.md`
- `docs/poc/onboarding-setup/03-unbound-events.jsonl`
- `docs/poc/onboarding-setup/03-unbound-stderr.txt`
- `docs/poc/onboarding-setup/04-readonly-answer.md`
- `docs/poc/onboarding-setup/04-readonly-events.jsonl`
- `docs/poc/onboarding-setup/04-readonly-stderr.txt`
- `docs/poc/onboarding-setup/05-no-project-md-answer.md`
- `docs/poc/onboarding-setup/05-no-project-md-events.jsonl`
- `docs/poc/onboarding-setup/05-no-project-md-stderr.txt`
- `docs/poc/onboarding-setup/06-auth-failure-answer.md`
- `docs/poc/onboarding-setup/06-auth-failure-events.jsonl`
- `docs/poc/onboarding-setup/06-auth-failure-stderr.txt`
- `docs/poc/onboarding-setup/07-invalid-address-answer.md`
- `docs/poc/onboarding-setup/07-invalid-address-events.jsonl`
- `docs/poc/onboarding-setup/07-invalid-address-stderr.txt`
- `docs/poc/onboarding-setup/08-no-github-connection-answer.md`
- `docs/poc/onboarding-setup/08-no-github-connection-events.jsonl`
- `docs/poc/onboarding-setup/08-no-github-connection-stderr.txt`
- `docs/poc/onboarding-setup/09-profile-reuse-answer.md`
- `docs/poc/onboarding-setup/09-profile-reuse-events.jsonl`
- `docs/poc/onboarding-setup/09-profile-reuse-stderr.txt`
- `docs/poc/onboarding-setup/10-profile-fix-intro-answer.md`
- `docs/poc/onboarding-setup/10-profile-fix-intro-events.jsonl`
- `docs/poc/onboarding-setup/10-profile-fix-intro-stderr.txt`
- `docs/poc/onboarding-setup/11-profile-fix-new-session-answer.md`
- `docs/poc/onboarding-setup/11-profile-fix-new-session-events.jsonl`
- `docs/poc/onboarding-setup/11-profile-fix-new-session-stderr.txt`
- `docs/poc/onboarding-setup/change-review.json`
- `docs/poc/onboarding-setup/change-review.md`
- `docs/poc/onboarding-setup/evidence-audit.json`
- `docs/poc/onboarding-setup/manifest.json`
- `docs/poc/onboarding-setup/plan.md`
- `docs/poc/onboarding-setup/profile-fix-diagnosis.json`
- `docs/poc/onboarding-setup/profile-fix-manifest.json`
- `docs/poc/onboarding-setup/profile-fix-validation.json`
- `docs/poc/onboarding-setup/profile-fix-verification.json`
- `docs/poc/onboarding-setup/profile-reuse-manifest.json`
- `docs/poc/onboarding-setup/report.md`
- `references/onboarding-setup.md`
- `references/project-context.md`
- `references/setup-profile.md`
- `scripts/read-profile.py`
- `tests/onboarding-setup.md`
- `tests/test_setup_profile.py`

## 排除项

个人profile.json、原始ACL备份、仓库外运行器、原始证据副本不纳入。下列既有旧诊断继续排除：

- `docs/poc/R8.1-first-mcp-write-commit-details.json`
- `docs/poc/R8.1-first-mcp-write-evidence.json`
- `docs/poc/R8.1-github-mcp-status.json`
- `docs/poc/R8.1-github-mcp-write-preflight-evidence.json`
- `docs/poc/R8.1-invocation-events.jsonl`
- `docs/poc/R8.1-invocation-preview.md`
- `docs/poc/R8.1-invocation-prompt.txt`
- `docs/poc/R8.1-invocation-stderr.txt`
- `docs/poc/R8.1-normal-session-events.jsonl`
- `docs/poc/R8.1-normal-session-read.md`
- `docs/poc/R8.1-normal-session-stderr.txt`
- `docs/poc/R8.1-record-preview.md`
- `docs/poc/R8.1-report.md`
- `docs/poc/R8.1-skill-discovery.json`
- `docs/poc/R8.1-write-final-preview.md`
- `docs/poc/R8.1-write-preparation.md`

## 本机权限变化（不纳入Git）

仅profile.json为CodexSandboxUsers增加Read允许项，无继承、无写入；父目录及全局策略未改。已有配置字节不变。
