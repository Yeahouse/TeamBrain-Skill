# TeamBrain Skill 开发工作区

源码仓库：https://github.com/Yeahouse/TeamBrain-Skill
独立测试数据仓库：https://github.com/Yeahouse/teambrain-test

项目理念：**每个人的 AI 搭档，整个团队的共同记忆。**

当前状态：查询与 Work Sync 基础功能已完成真实MCP验收，第三个入口 Onboarding & Setup 已完成基础验收及跨会话个人配置复用修复。本机 Skill 目录链接直接引用本工作区，源码修改无需复制同步。

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

查询前先明确本次项目；历史示例Yeahouse/teambrain-test不是默认绑定。在正常 Codex 对话直接说：

- TeamBrain，介绍一下当前项目。
- TeamBrain，现在项目进展如何？
- TeamBrain，测试成员 A 做了什么？
- TeamBrain，查看 R8.1 阶段的记录。
- TeamBrain，有哪些已提交的成果？

Skill 通过 MCP 读取 project.md、records/、artifacts/、links/ 及记录关联附件，按现有远端数据回答。缺失目录不会自动创建；未找到记录不代表成员未开展工作。默认简洁并提供来源路径。项目绑定见 references/project-context.md，查询规则见 references/project-progress-query.md。

原 github 只读连接曾认证失败；当前可选用已授权测试连接的 get_file_contents。查询不调用写工具。正常桌面/CLI 进程须能继承 MCP 令牌环境；令牌不存放于 Skill。其他团队使用前应指定自己的共享仓库，不能沿用本测试绑定。

本轮验收及原始证据保存在 docs/poc/project-progress-query/；验收状态以其报告为准。开发记录提交、推送需用户确认。

## Work Sync（智能阶段工作同步）

在阶段工作结束后直接说：“TeamBrain，帮我同步一下刚刚完成的工作。”

AI 仅提炼当前可见对话，整理工作、方案取舍、正式结论或探索状态，识别文本成果和外部链接，先展示记录及目标路径。可修改、排除或取消；明确确认后才通过 MCP 提交并回读。不上传整段聊天、不主动读取其他历史会话。PDF/DOCX/PPTX 当前只识别候选，不自动上传。

流程：references/work-sync.md；本地草稿辅助：references/work-sync-draft.md、scripts/prepare-work-sync.py。辅助脚本只产生待确认包，不连接 GitHub。测试使用本轮用户明确授权的仓库，沿用既有 R7 结构，不沿用历史默认项目。

重复请求保留ID并查远端，内容一致则不重复写；冲突或结果未知先核对，不自动覆盖或盲目重试。验收状态见 docs/poc/work-sync/，预览通过不能等同完整同步通过。


## 首次使用与项目连接

直接说：“TeamBrain，请介绍你的功能。”

V3.1先介绍“了解团队进展、记录并分享自己的工作、查找并利用已有成果”及自然语言示例，再说明首次使用可能需要GitHub连接检查，并询问是否开始；单纯介绍不读取个人配置、不调用GitHub。用户明确连接/检查时才进入现有Onboarding，只询问缺少的信息。项目与成员已确认时可直接使用；只读连接仍可查询，不能据此默认可以上传。缺少project.md时根据现有README/记录说明能确认什么，不自动初始化仓库。

当前成员的工作署名由本人确认，不能从仓库owner、GitHub账号或虚构测试作者猜测。每位成员使用自己的GitHub授权与本地配置；不共享令牌。GitHub连接、项目绑定和成员身份分别管理；凭据不存入Skill或项目仓库。

可选本地个人配置及检查流程见 references/setup-profile.md 与 references/onboarding-setup.md。任何新建仓库、权限变更或真实上传都另行确认。代码不包含独立后端或前端。实际验收范围与限制见 docs/poc/onboarding-setup/report.md。


V3.1触发与默认完整文案见 references/first-introduction.md。已确认项目的查询和同步直接执行原流程；仅有旧配置时先确认本次目标；“暂不连接”正常结束。配置数据结构、GitHub存储架构和同步算法不变。此轮开发仅本地，验收见 docs/poc/v3.1-introduction/report.md，未自动提交推送。


## V3.2：本地多项目与成员身份

可以直接说“TeamBrain，我有哪些项目？”“添加一个新项目”“切换到某项目”“查看我在当前项目的身份”“我在这个项目中叫…”。各仓库独立保存项目名称、分支及成员署名/可选角色；同名项目用owner/repo区分。添加、保存默认项目及改署名先展示预览，确认后本地保存，不修改远端。

继续兼容原version=1配置，复用scripts/read-profile.py，不重复建立配置系统。查询与同步共用resolve：当前指令指定目标优先于会话已确认目标，历史默认只作候选，跨会话可以列出并恢复，但不能猜测本次工作归属。完整规则见references/project-management.md、project-context.md和setup-profile.md。本地绑定、MCP可调用和GitHub读写权限分别判断。V3.1功能介绍不主动读配置。

V3.2验收及未验证项见docs/poc/v3.2-projects/report.md。本轮不提交推送，不自动修改真实个人配置、安装或GitHub数据。


## V3.3：连接与成员权限引导

说“TeamBrain，检查我的项目连接”，在确认本次项目后检查真实GitHub MCP及仓库读取能力，分别说明只读限制、写能力未验证、认证/环境/授权范围问题。管理员邀请、成员接受与个人授权分开引导；有效授权直接复用，不要求所有成员新建Token，不试写、不自动扩权。具体规则见references/github-connection.md；变量诊断辅助脚本仅检查名称存在性，不读取秘密值。本轮仅最小安全检查，未完整CLI验收或验证跨账号加入/写入。
