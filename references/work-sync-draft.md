# 本地草稿包

当需要稳定 ID、候选附件指纹和可复核的提交内容时，用 scripts/prepare-work-sync.py。它不上传任何内容；用户确认和 MCP 写入仍由当前会话按 work-sync.md 执行。

将提炼结果保存为本地 JSON，建议使用已忽略的 tmp/work-sync/，不要保存原始聊天或令牌。调用：

`python scripts/prepare-work-sync.py --input <draft.json> --output <packet.json>`

输入字段：request_key（本次请求稳定标识）、author、stage、topic、kind（decision/exploration）、work（列表）、discussion（列表）、conclusions（列表）、open_questions（列表）、artifacts（path/name 项列表）、links（name/url/verified 项列表）；可选 submission_id、occurred_at。工作时间未提供则明确标记未提供，不冒用上传时间；created_at 是包生成时间，带 +08:00。

探索记录允许 conclusions 为空；正式结论记录必须提供 conclusions。path 是本地真实文件；name 仅为安全文件名，不含目录跳转。仅支持 UTF-8 的 .md/.markdown/.txt；其他类型由 AI 在候选清单标记待支持，不传给文本上传包。

输出包含稳定 ID、request_key、request_fingerprint、record_content、files（path/content）、artifact_manifest、links、state=awaiting_confirmation。同一个输出文件和 request_key 重建时保留 ID 与创建时间；不同 request_key 不允许覆盖同一输出包。修订会更新指纹并回到待确认状态。新请求必须使用新输出文件，不能从旧包复制确认状态。

确认前只展示输出，不调用 push_files。确认后只把 files 与 owner/repo/branch/message 组成 MCP 参数，绝不将整个 packet（包括本地路径）上传。确认回执单独记录，不伪造上传/核验状态。

脚本内 evaluate_receipt(write_outcome, remote_state) 可用于本地运行回执判定：返回是否可以报告成功及下一步行动，不执行网络或重试。success/rejected/unknown 分别代表写入工具结果；remote_state 必须来自实际回读（或明确标注未检查/不可读）。开发单元测试使用受控输入检查失败与未知状态分支，不冒充 GitHub 实际故障。
