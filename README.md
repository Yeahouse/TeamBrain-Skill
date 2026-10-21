# TeamBrain Skill 开发工作区

源码仓库：https://github.com/Yeahouse/TeamBrain-Skill
独立测试数据仓库：https://github.com/Yeahouse/teambrain-test

当前状态：R8.1 首次 MCP 读写闭环已实测通过；第一个核心功能“项目进展与成员工作查询”已通过五条正常会话实测（当前单记录虚构数据集）。本机 Skill 目录链接直接引用本工作区，源码修改无需复制同步。

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


## 项目进展与成员工作查询

当前开发测试目标为 Yeahouse/teambrain-test（main）。在正常 Codex 对话直接说：

- TeamBrain，介绍一下当前项目。
- TeamBrain，现在项目进展如何？
- TeamBrain，测试成员 A 做了什么？
- TeamBrain，查看 R8.1 阶段的记录。
- TeamBrain，有哪些已提交的成果？

Skill 通过 MCP 读取 project.md、records/、artifacts/、links/ 及记录关联附件，按现有远端数据回答。缺失目录不会自动创建；未找到记录不代表成员未开展工作。默认简洁并提供来源路径。项目绑定见 references/project-context.md，查询规则见 references/project-progress-query.md。

原 github 只读连接曾认证失败；当前可选用已授权测试连接的 get_file_contents。查询不调用写工具。正常桌面/CLI 进程须能继承 MCP 令牌环境；令牌不存放于 Skill。其他团队使用前应指定自己的共享仓库，不能沿用本测试绑定。

本轮验收及原始证据保存在 docs/poc/project-progress-query/；验收状态以其报告为准。开发记录提交、推送需用户确认。
