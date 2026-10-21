已实际使用安装路径中的 TeamBrain Skill，并通过当前 GitHub 工具读取 `Yeahouse/teambrain-test/main`，检查结果如下：

| 检查项 | 当前状态 |
|---|---|
| Skill | 已读取入口及 Onboarding 配置说明，可用 |
| GitHub 连接 | `github_test_write` 的读取工具调用成功 |
| 项目绑定 | 本次会话已确认目标；本地 `profile.json` 不存在，未持久保存 |
| 仓库读取 | 根目录、README、records 目录均读取成功，查询可用 |
| 正式项目说明 | 根目录没有 `project.md`；README 明确为虚构数据及 PoC 测试仓库 |
| 写入工具 | 当前提供 `push_files` |
| 实际写权限 | 未验证，未试写；工具存在不代表令牌及分支允许写入 |
| 成员身份 | 正式署名待本人确认；GitHub 登录身份未核实，不影响查询 |

依据当前 [README](https://github.com/Yeahouse/teambrain-test/blob/main/README.md)，不能据此推断正式项目目标、完整成员名单或阶段规划。`records/` 有记录目录，但本轮未读取其中正文，不能宣称它们证明了当前进展或同步成功。

可以直接使用：

- `TeamBrain，介绍 Yeahouse/teambrain-test/main，只依据实际资料，区分测试内容与正式项目信息。`
- `TeamBrain，查询 Yeahouse/teambrain-test/main 的 records，总结已有记录及来源，缺失信息明确标注。`
- `TeamBrain，整理刚刚完成的工作，仅生成同步预览；署名暂留待确认，不保存配置、不上传。`

本轮没有写入任何文件、保存测试署名、创建仓库或修改权限，也未访问其他仓库或用旧测试报告替代实测。