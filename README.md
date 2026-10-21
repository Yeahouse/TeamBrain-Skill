# TeamBrain Skill 开发工作区

源码仓库：https://github.com/Yeahouse/TeamBrain-Skill
独立测试数据仓库：https://github.com/Yeahouse/teambrain-test

当前状态：R8 最小开发骨架，尚未完成行为验证。开发目录不等于已经安装的 Skill；本次不修改全局 Codex 配置。

## 文件导航

- SKILL.md：Skill 入口与最小工作流程。
- references/record-format.md：PoC 记录格式。
- scripts/Get-ArtifactFingerprint.ps1：计算附件大小及 SHA-256。
- docs/adr/0001-two-repositories.md：双仓库决定。
- docs/R8.1.md：验证路线。
- docs/poc-log.md：开发与验证证据。
- docs/first-push.md：首次推送及日常备份教程。
- tests/manual-cases.md：手工验收用例。

先完成 R8.1，再根据实测决定是否添加上传脚本。不要上传密码、令牌或真实团队敏感数据。
