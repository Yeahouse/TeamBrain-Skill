> 最新状态：用户已明确批准三份完整预览，三条记录共5文件已通过MCP写入与固定提交核验。见 [write-results.md](write-results.md)。下文原有“待确认/尚未写入”内容保留为上传前验收快照。

# Work Sync 基础功能：开发与预确认验收

日期：2026-10-21（Asia/Shanghai）。状态：基础实现完成，尚未获得三条具体草稿的上传确认；未将预览成功记作完整同步通过。

## 前置查询提交已完成

用户批准的 26 个文件经哈希、敏感信息与暂存清单复查，以指定说明提交并推送 main。Commit 为 3bf9aa3db87cfdf0e01e80575b26e5f054866b21，实际26文件，远端 main 与本地一致；没有混入其他旧诊断材料或仓库外原始证据。

https://github.com/Yeahouse/TeamBrain-Skill/commit/3bf9aa3db87cfdf0e01e80575b26e5f054866b21

## 本轮实现

保持原工作区和 R7 信息结构。SKILL.md 新增 Work Sync 路由；references/work-sync.md 定义当前可见对话提炼、真实成果候选、结论/探索区分、预览修改取消、MCP查重、提交回读和失败恢复边界。

scripts/prepare-work-sync.py 仅生成本地待确认包，不联网。为新请求生成ID；同一request_key修订保持ID并更新指纹；取消包拒绝自动恢复。记录是 Markdown；附件只支持实际可读UTF-8文本，保持原字节与SHA-256；外链保留用户提供地址且不虚报访问。常见凭据与含授权参数链接不能进入待提交包。PDF/DOCX/PPTX保留候选识别入口，不做自动上传。

运行回执函数只在远端内容全部一致后允许报告成功；写入拒绝、未检查、不可读、部分内容或差异均不会虚报成功，未知结果要求先查远端再决定。该函数不发请求或重试。

## 真实 Skill/MCP 验收

正常Codex用户配置、Windows沙箱、无模型覆盖。测试输入是当前用户消息中明确提供的虚构工作信息，不读取其他历史聊天。运行时将测试连接工具限制为 get_file_contents；实际没有远端写工具调用。初始回合读取 Skill/引用文件并调用MCP，同一修改/取消会话的后续回合复用已加载上下文。没有用Git CLI代替MCP或上传完整对话。

| 真实回合 | MCP读取数 | 实际回答 | 调用事件 |
| --- | --- | --- | --- |
| 01-normal | 4 | [01-normal-answer.md](01-normal-answer.md) | [01-normal-events.jsonl](01-normal-events.jsonl) |
| 02-revised | 4 | [02-revised-answer.md](02-revised-answer.md) | [02-revised-events.jsonl](02-revised-events.jsonl) |
| 03-exploration | 4 | [03-exploration-answer.md](03-exploration-answer.md) | [03-exploration-events.jsonl](03-exploration-events.jsonl) |
| 04-edit-cancel | 4 | [04-edit-cancel-answer.md](04-edit-cancel-answer.md) | [04-edit-cancel-events.jsonl](04-edit-cancel-events.jsonl) |
| 04b-edit | 0 | [04b-edit-answer.md](04b-edit-answer.md) | [04b-edit-events.jsonl](04b-edit-events.jsonl) |
| 04c-cancel | 1 | [04c-cancel-answer.md](04c-cancel-answer.md) | [04c-cancel-events.jsonl](04c-cancel-events.jsonl) |
| 05-duplicate | 6 | [05-duplicate-answer.md](05-duplicate-answer.md) | [05-duplicate-events.jsonl](05-duplicate-events.jsonl) |
| 05b-exact-duplicate | 2 | [05b-exact-duplicate-answer.md](05b-exact-duplicate-answer.md) | [05b-exact-duplicate-events.jsonl](05b-exact-duplicate-events.jsonl) |

### 场景结果

1. 正常结论：实际提炼独立记录方案、未验证并发、79字节真实文本成果，生成稳定UUID草稿；预览通过，写入与回读待用户批准后执行。
2. 多次修订：正确区分共享总文件已否定、数据库暂不采用、独立Markdown最终决定，没有补造数据库被否定原因；预览通过，完整同步待确认。
3. 探索记录：没有实验或正式结论，明确标为探索，不把未选定方案当正式决定，排除result.txt。最终确认包不含附件，完整同步待确认。
4. 修改与取消：同一真实会话先预览，再修改未决问题、仅保留result.txt，记录ID不变；再取消，本地包state=cancelled，真实MCP读取records确认远端不存在该ID。通过；没有用写入证明取消。
5. 重复/冲突：首轮输入里“Work Sync验收”阶段与R8.1已有记录不同，AI报告冲突并停止，没有假称内容一致。保留该真实结果；随后追加精确正文/附件对照，通过MCP回读，确认逐字一致、73字节及SHA-256一致，引用已有提交b635a62051d3ad6e8988f772be1fa6c4b97f571e，不创建新ID、不重复上传。两个保护分支均有独立证据。

本地单元测试10项通过，证据unit-tests.txt：唯一ID、稳定修订、缺信息、取消阻断、探索标记、附件字节/路径/二进制阻断、外链状态与授权参数阻断、常见凭据阻断、明确拒绝及未知/未核验回执分支。失败与网络分支使用受控输入，不是GitHub实际故障实测。

## 待确认上传包

见 pending-upload-previews.md（完整正文与附件）和 pending-upload-manifest.json（精确路径及内容指纹）。三条包均为 awaiting_confirmation；共5个文件。案例2、3的最终包是在原实际AI预览基础上整理出的本次完整版本，最终以本文件列出的完整预览供用户确认。

目标仅 Yeahouse/teambrain-test/main。取消包与原重复记录均不进入清单。任何“继续开发”不等于批准尚未展示的包；等待用户针对这三条内容明确确认。确认后仍先MCP重查最新目标路径，冲突停止，逐包一次提交、按固定提交SHA回读核验。

## 限制与未测试事项

- 本轮尚未上传这三条Work Sync记录，完整“提炼→确认→写入→回读”验收仍未完成；原R8.1基础写入成功不能替代本功能验收。
- GitHub真实写入失败和网络断开后的恢复未实测；本轮只通过本地回执分支与已有远端记录比对验证安全规则。
- 没有复杂并发、自动项目管理、PDF或其他二进制上传。
- 原github只读连接曾持续认证失败，本轮使用已授权测试连接的读取工具，未改变令牌权限或持久MCP配置。
- 当前文本包不自动检验语义真伪；当前AI须依据可见上下文提炼并由用户预览确认。常见凭据扫描不能替代人工敏感信息审阅。
- 提交前已将CLI日志本机路径、临时授权参数及提交元数据中的电子邮件脱敏；未经脱敏的原始副本保留仓库外，不随提交上传。

## 本轮修改文件

- SKILL.md：Work Sync自然语言入口与路由。
- references/work-sync.md、references/work-sync-draft.md：完整流程和本地包约定。
- scripts/prepare-work-sync.py：本地待确认包与运行回执判定。
- tests/test_work_sync.py、tests/work-sync.md：脚本与行为验收。
- README.md、docs/poc-log.md：使用方法和开发进度。
- docs/poc/work-sync/：计划、真实回合回答/事件、清单、受控测试、待确认完整预览及本报告。
- tmp/work-sync-acceptance/：已忽略的本地测试输入和包，不纳入开发提交。

开发成果未暂存、提交或推送；用户批准前无新的远端记录。后续先完成三条明确批准的同步验收，再按真实结果更新报告，另行请求开发成果的提交确认。


# Work Sync：三条批准记录的实际写入与固定提交回读

测试日期：2026-10-21（Asia/Shanghai）。结论：本次三条虚构记录的提炼、预览、用户明确确认、MCP写入及回读核验闭环通过。

## 执行前核对

三份包的记录ID、文件清单、每份文件的UTF-8字节数与SHA-256均匹配此前审核manifest。重新渲染完整预览，与已审核预览文件按实际换行编码比较一致。附件还与实际本地result.txt字节比较一致。没有修改已批准正文、路径或文件清单。

内容检查未发现已配置令牌值、常见GitHub凭据、认证头、私钥或个人绝对路径。目标固定为 Yeahouse/teambrain-test/main。通过MCP读取最新README与records目录，初始提交为 b635a62051d3ad6e8988f772be1fa6c4b97f571e；每条提交前再次读取records，目标ID目录均不存在，因此不存在覆盖已有路径。没有额外失败注入。

## 实际提交结果

| 记录ID | 文件数 | Commit ID | 链接 | 固定提交校验 |
| --- | --- | --- | --- | --- |
| ws-fde7b652b4cb49789bcab59f0ccd1881 | 2 | `954b9fa8c2940287852ac09050be549c19d4df56` | [查看提交](https://github.com/Yeahouse/teambrain-test/commit/954b9fa8c2940287852ac09050be549c19d4df56) | 通过 |
| ws-729b22e4048f4b4b8580ebf7f9f25e61 | 2 | `923a6d96a70067460c96862627aa9842f4fe9295` | [查看提交](https://github.com/Yeahouse/teambrain-test/commit/923a6d96a70067460c96862627aa9842f4fe9295) | 通过 |
| work-sync-20261021-a-7f942c | 1 | `d3133bda9a8b37a50cb6637e401bf565a48f1842` | [查看提交](https://github.com/Yeahouse/teambrain-test/commit/d3133bda9a8b37a50cb6637e401bf565a48f1842) | 通过 |

三次实际 push_files 调用，每条仅尝试一次，共新增5文件。MCP get_commit 分别确认各提交只含批准文件，状态均为added。未使用Git CLI代替写入、未操作其他仓库。

## 回读与内容验证

每次提交后，先从main读取，再按写入响应中的固定Commit ID重新读取全部文件，并校对资源URI中的提交SHA。三份Markdown正文逐字节一致，字节数分别为1139、1043、907。

两份result.txt均为79字节；SHA-256均为：

`3a76f798bd7210c89f063ba3378e76987da831bbb49cbd44180279a27cac0048`

两份附件远端UTF-8字节与各自批准包及本地原文件完全相同。探索记录只有record.md，没有新增附件。

原始MCP请求、提交响应、固定提交返回正文与文件校验摘要：approved-write-evidence.json。临时下载授权参数如有返回则已脱敏，没有保存授权头或令牌。GitHub提交明细可能包含账号的公开提交元数据，开发报告未来发布前仍须进行范围和敏感信息复查。

本地包state已改为verified并保存Commit回执，未改动包内已批准files内容；远端Markdown保留“提交前内容快照、真实结果另记回执”的表述，没有为更新状态再追加提交。

## 验收结论与边界

- 正常结论、多次修订方案、探索记录三个场景现已完成真实写入与回读。
- 修改/取消和精确重复/冲突保护沿用本轮前面的真实Skill/MCP测试证据，取消包未上传、已有记录未重写。
- 本轮五个基本功能场景已覆盖；10项本地可靠性测试通过。
- 本次未出现写入冲突、网络异常或未知提交状态，没有重试、没有额外故障注入。真实GitHub写入拒绝和断网恢复仍未实测，不能将本地受控状态测试冒充实际故障通过。
- 不覆盖复杂并发压力、PDF/DOCX/PPTX上传、跨会话自动提炼或自动项目管理。

开发工作区只保存本地报告与证据，未暂存、未提交、未推送TeamBrain-Skill。本地测试仓库克隆未自动更新，本次结果均以MCP远端读取为准。
