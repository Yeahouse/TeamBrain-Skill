# Project Progress Query：首个核心功能交付与实测

日期：2026-10-21（Asia/Shanghai）。状态：本地开发完成、五条实测通过；未提交、未推送开发仓库。

## 功能实现

沿用现有 Skill，在入口的描述与查询路由中补齐自然语言查询触发；新增两个按需读取的参考文件，分别绑定用户确认的唯一测试仓库和定义查询规则。没有新增数据库、同步服务或独立应用，也没有重复实现已有的阶段保存流程。

支持项目总体介绍/进展、指定成员、指定阶段、已提交成果查询。通过 MCP 获取目录和记录，以作者/阶段内容字段筛选，核对实际附件目录并给出固定提交来源。缺失记录不等于没工作；缺少正式项目说明不补造目标、成员名单或完成率。

R7 的 project.md、records/、artifacts/、links/ 结构保留；兼容现有 records/<id>/artifacts/ 引用，不迁移远端文件。当前仓库没有 project.md 或根 artifacts/、links/，查询说明其缺失而不补建。fixtures 不作为工作成果。

## 真实测试环境

五条指令分别运行正常 Codex CLI 会话：保留用户配置与 Windows elevated sandbox，使用 workspace-write 模式；没有使用 --ignore-user-config，也没有绕过沙箱。没有改模型设置。

输入为表中的自然语言原句，另加统一只读验收边界（实际使用 MCP、不修改文件/远端、不读取其他项目、不以本地报告代替远端数据）。没有预注入期望回答、远端正文或强制 $teambrain。每个用例的事件都观察到实际读取 SKILL.md 及 project-progress-query.md，并完成测试仓库的阶段记录 MCP 读取。

运行时关闭原认证异常的 github 和无关连接，对 github_test_write 临时设置 enabled_tools 仅 get_file_contents。用户的持久 MCP 配置和授权未修改。原始事件记录包括调用参数、远端返回内容、执行状态和最终回答。

数据快照为 b635a62051d3ad6e8988f772be1fa6c4b97f571e。只有测试成员 A 的一条 R8.1 虚构记录及 sample.txt（73 字节）。测试没有生成新的远端记录或假设存在其他成员。

## 五条查询验收

| 指令 | 人工审阅 | 实际 MCP 调用数 | 本次耗时 | 回答与事件证据 |
| --- | --- | --- | --- | --- |
| TeamBrain，介绍一下当前项目。 | 通过 | 6 | 79.0 秒 | [01-answer.md](01-answer.md) / [01-events.jsonl](01-events.jsonl) |
| TeamBrain，现在项目进展如何？ | 通过 | 6 | 81.9 秒 | [02-answer.md](02-answer.md) / [02-events.jsonl](02-events.jsonl) |
| TeamBrain，测试成员 A 做了什么？ | 通过 | 5 | 76.4 秒 | [03-answer.md](03-answer.md) / [03-events.jsonl](03-events.jsonl) |
| TeamBrain，查看 R8.1 阶段的记录。 | 通过 | 6 | 63.4 秒 | [04-answer.md](04-answer.md) / [04-events.jsonl](04-events.jsonl) |
| TeamBrain，有哪些已提交的成果？ | 通过 | 6 | 59.5 秒 | [05-answer.md](05-answer.md) / [05-events.jsonl](05-events.jsonl) |

共 29 次 MCP get_file_contents 调用：28 次成功；项目介绍用例另有一次缺失 project.md 的读取返回失败，回答正确说明缺少正式项目定义，没有将其当作项目未开展。所有 MCP 调用均限定 owner=Yeahouse、repo=teambrain-test，没有写工具调用。

人工逐条对照已回传的记录正文及目录响应：

- 项目介绍与进展没有捏造目标、成员或完成率，明确虚构测试属性。
- 成员查询按记录作者归属，未把 GitHub 提交者当作工作作者。
- 阶段查询正确返回 R8.1，保留并发未验证与 R8.2/R8.3 未执行的信息。
- 成果查询列出记录与确实存在的 sample.txt，引用来源；没有把 fixture 或 README 当成果，未声称本轮做了 SHA-256 校验。
- 均区分文件现已远端可读与正文中旧的“待执行”状态快照。

机器核查见 evidence-audit.json，包含每例实际读取路径和范围门槛；manifest.json 保留指令、运行设置、耗时及本次 Skill 文件哈希。该机器核查不能替代上述人工内容审阅。

## 问题与限制

1. 原 github 只读连接本轮重新实测仍为 Auth required、0 工具，见 original-readonly-connection-check.json。当前可用测试连接的读取工具足以完成此功能；没有擅自修改认证。后续建议由用户重新签发原连接最小范围只读 PAT，更新原环境变量并重启继承环境，再通过 MCP 重验。不要为了查询扩大任何仓库权限。
2. 缺少 project.md，无法验证基于正式目标、完整成员名单和阶段规划的正向汇总。该分支已实现规则，但本轮实际覆盖的是缺失说明的降级行为。
3. 测试数据只有一名虚构成员、一个阶段、一份文本附件；多成员别名、多个阶段、矛盾记录、大仓库分页和未知成员的无记录分支尚未逐项实测。不宣称全量场景通过。
4. 单条测试约 59–82 秒，包含独立 CLI 启动与模型/MCP 往返；不是纯查询接口耗时。后续可减少重复读取、按快照复用同一会话已读信息，但不能拿旧缓存冒充最新进展。
5. 当前测试连接具有写权限，查询验收在进程工具白名单层仅开放读取，Skill 本身也要求只读。其他正常会话仍须按查询指令执行，长期使用建议恢复独立只读连接。
6. 已脱敏证据中的临时下载授权参数，检查未发现已配置令牌值；CLI 事件的个人路径已替换为占位符；原始日志副本保留在 Git 仓库外，不随提交上传。

## 本轮文件清单

- 修改 SKILL.md：自然语言查询描述与路由。
- 新增 references/project-progress-query.md：真实读取、筛选、成果解析、来源与不确定性规则。
- 新增 references/project-context.md：当前测试目标和已授权读取连接。
- 修改 README.md：当前状态、五种查询用法及环境要求。
- 新增 tests/project-progress-query.md：行为验收标准。
- 修改 docs/poc-log.md：纳入 R8.1 已通过闭环与本轮查询实测。
- 本目录新增五份 answer.md、五份 events.jsonl、五份 stderr.txt、manifest.json、evidence-audit.json、original-readonly-connection-check.json 和本报告。

之前 R8.1 首次写入报告与证据继续保留本地，见上一级 R8.1-first-mcp-write-report.md。它们不等于本轮新增查询数据，也没有自动提交。

## 下一轮智能进展同步建议

先实现一个最小新增记录流程：从当前对话提炼作者、阶段、结论与真实成果 → 展示草稿、目标仓库和路径 → 用户确认 → 检查重复 ID/最新状态 → MCP 文本提交 → 固定提交回读。复用现有保存规则和 R8.1 已验证的工具，不重建信息结构。

优先处理记录中“提交前状态快照”与后续核验结果的表达，避免查询时将旧待执行字段误当当前失败；保留核验记录来源。附件初期只处理已有可读文本；PDF、后台同步和复杂并发继续不做。正式项目基础说明 project.md 的创建或填充需先取得用户对内容的确认，不能由查询功能自动补写。

本轮停在用户审阅阶段；不暂存、不提交、不推送。
