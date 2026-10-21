# GitHub MCP 连接、仓库权限与成员加入

用于“检查我的项目连接”“GitHub连不上”“加入团队/没有权限/配置Token”等请求。先按project-context.md确定目标；只有历史配置时先选项目，不枚举其他仓库。单纯功能介绍不执行本流程。所有检查只读，不创建Token、不邀请成员、不修改授权、MCP或环境配置。

## 先检查已有连接

发现当前会话实际可调用的GitHub MCP工具，含延迟工具目录；不要只看配置文件中的服务器名称。preferred_connection只是候选，可复用其他已授权且能访问同一目标的GitHub MCP连接。ChatGPT GitHub应用/插件、gh/Git登录与GitHub MCP是不同通道，不能据前者正常就宣布MCP正常；本流程不默默切换成Git CLI或插件代测。若已有MCP读取成功，直接复用，不要求新Token或环境变量检查。

工具不见时才按需要检查本地有效配置与启动错误，只输出服务器名、enabled、传输类型、环境变量引用名、工具允许/禁用状态。配置路径依环境确定：Codex用户级通常为CODEX_HOME/config.toml（未覆盖时为~/.codex/config.toml），还可能有受信任项目配置、运行时覆盖或插件服务器。不能只因某一文件缺少条目就断言未配置；无法检查其他配置源时标明“当前会话不可见，配置来源尚未确认”。不输出完整配置、env、http_headers、认证缓存或原始启动日志；确需本机解析时仅投影非敏感字段，绝不读取凭据值或运行会回显凭据的诊断命令。

| 证据 | 判断及下一步 |
| --- | --- |
| 有效配置确认无服务器，工具也不存在 | 未配置；先介绍连接方案，获得配置修改批准后才配置 |
| 服务器被禁用或工具被白名单过滤 | 当前会话不可用；不是认证失败，先说明需要启用的最少工具 |
| 启动明确报缺少被引用变量，或仅名称检查显示进程缺失 | 缺启动环境；不据此判Token过期。用户环境有而进程无时，通常需完全退出并重启宿主以继承新环境，不能断言任意既有桌面进程状态 |
| 401 / 明确Auth required / Bad credentials | 认证缺失或失败；无法仅由401区分过期、撤销或错误Token，按实际授权方式重新授权 |
| 403且提示Resource not accessible by personal access token/integration | 当前凭据/组织策略限制；检查选定仓库、Contents权限、组织审批/SSO，不自动扩大授权 |
| 403/429且明确限流 | 请求暂受限，按重试提示等待；不是成员被移出或Token过期 |
| 超时、DNS、握手失败 | 网络/传输故障，认证和仓库权限未知；不自动重装或改Token |

变量诊断仅针对实际配置引用的名称（bearer_token_env_var、env_http_headers的变量名、stdio所需变量）。可运行Skill下`scripts/check-mcp-env.py NAME [NAME ...]`，只输出当前检查子进程中的名称存在性，以及Windows当前执行身份持久环境中该名称是否存在；不读变量值、不检查全部凭据。存在不保证非空、有效或被MCP采用。沙箱可能使用另一个Windows身份，此时注册表结果不能代表桌面登录用户；不要据其缺失断言用户未持久配置。当前子进程不等于另一个已启动桌面进程；内联env、OAuth、凭据助手、远程执行环境不能套用此检查，无数据则标未知。脚本不改任何环境。不得运行Get-ChildItem Env:、set或输出Token长度/哈希，也不得读取认证缓存。

## 目标仓库与权限

用get_file_contents只读列出明确目标根目录，优先选定分支；文件缺失时不要把单个project.md/README的404当仓库不存在。必要时仅对同一仓库用默认分支根目录再核对一次，区分分支错误与仓库不可达；不扫描其他仓库。空仓库/空分支若有明确empty repository证据，说明可访问但无项目内容，不初始化。

| 状态 | 可报告内容 |
| --- | --- |
| 读取成功 | 本次MCP可调用、目标内容可读；查询可用，成员身份与写权限另列 |
| 根目录404、原因不明 | “目标暂不可访问，可能地址/分支错误或当前账号/凭据无权访问”；请核对地址、邀请及授权范围，不说不存在 |
| 管理员独立确认地址已删除/不存在 | 才可称仓库不存在，并注明来源；不创建替代仓库 |
| 明确禁止或授权缺范围 | 权限不足；分清账号访问权、Token范围、组织审批与连接只读限制。仅同一账号网页可访问而MCP失败只能说明当前凭据/策略待查，不能直接证明Token选仓库错误 |
| 只有读取工具或明确只读模式/Contents只读 | 当前连接只读，查询可用，不能同步；不推断该成员所有连接都无写权限 |
| 有push_files但无可信写权限证据 | “查询可用；写工具可见，写权限未验证”，不能报告可写 |
| 同一账号/凭据/仓库的当前元数据明确允许Contents写入，且连接允许push_files | “授权层面支持写入，目标分支规则及实际同步仍待确认”；账号push角色单独不足以证明Token能力 |
| 本次经用户批准的实际写入并回读成功 | 才说该次目标路径/分支写入已验证，不把过去成功永久缓存为可写 |

有效同步取决于账号角色、凭据范围、服务器只读设置、客户端工具策略和目标分支规则共同允许。没有足够工具或响应就保持“未验证”。不调用push_files探测权限，也不自动开放metadata/admin工具、创建分支或绕过保护。可准备本地草稿；实际同步仍必须走原Work Sync完整预览确认。

## 成员加入：三个不同步骤

1. 管理员在目标仓库/组织按需要邀请该成员的GitHub账号并授予合适角色；本Skill只说明，不代发邀请或改角色。
2. 成员以被邀请账号接受邀请；邀请已发送不等于接受，也不等于Token已覆盖该仓库。组织团队/SSO策略可能还需管理员处理。
3. 成员在自己的AI环境使用自己的GitHub授权连接MCP，再实际只读检查目标。不能共享管理员Token；Github账号不能替代TeamBrain该项目已确认署名。可用身份只读工具时才核实GitHub账号，不为核实身份额外要求admin权限；工具不支持时说账号未核实。

可请成员用自己的GitHub账号在网页核对仓库/邀请状态，但这不代替MCP实际读取。不要从404推断邀请未接受，也不要因公开仓库可读推断成员已加入或写权限有效。只读成员可查询，上传时明确说明当前缺哪层写能力。

## 仅在确需时引导授权

先复用有效OAuth、GitHub App或既有PAT；不是每人都要新建Fine-grained PAT。需要PAT且用户决定配置时：GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens；选实际有权限的Resource owner，Only select repositories仅目标仓库、短有效期；查询Contents: Read-only，同步需Contents: Read and write，Metadata自动Read-only，其余不增加。组织审批/SSO及资源所有者限制按页面实际提示处理。

Fine-grained PAT并不覆盖所有协作者场景；无法选择他人的个人仓库或组织outside collaborator受限时，不循环要求重建，也不擅自改为更宽classic PAT。说明限制，评估该环境确实支持的OAuth/GitHub App等方式，方案/权限调整需用户批准。Token不能赋予账号本身没有的访问权限。

Remote官方地址为https://api.githubcopilot.com/mcp/，Codex PAT方式用bearer_token_env_var引用现有变量名；按需要只开放get_file_contents和（用户确需同步时）push_files。env_http_headers也引用变量名，不内嵌Authorization。示例只供用户批准后配置，不自动执行：

```toml
[mcp_servers.github_team]
url = "https://api.githubcopilot.com/mcp/"
bearer_token_env_var = "TEAM_GITHUB_TOKEN"
enabled_tools = ["get_file_contents"]
```

不要覆盖已有同名条目、只读连接或其他仓库配置。具体地址、白名单与现有认证方式须匹配实际环境，配置存在不代表已可调用。需要用户设置秘密时，让其在本机受信任的隐藏输入/凭据管理界面自行完成，不粘到聊天、终端命令参数、项目.env或profile。需要用户级持久环境设置时先说明仅新增/更新哪一个变量并取得批准，提醒其不是加密保险箱；本Skill不自动读出、迁移或持久化Token。重启后重新发现工具并只读检查同一目标；本轮不自动配置Docker或认证系统。

## 面向用户的回复

简短说明项目/分支、查询结果、同步状态、成员状态和一项下一步，按证据调整，例如：

“项目能正常读取，可以查询团队进展。当前连接提供写入工具，但写权限还未验证；不会进行试写。你的项目署名已保存。需要同步时，我会先展示内容和目标，等你确认。”

或：“目前无法读取这个仓库，还不能确定是地址问题还是授权范围不足。请先确认该GitHub账号已接受团队邀请；不需要发送Token。”

不展示原始JSON或大段错误，不把未执行步骤写成已完成。若目标未明确，唯一下一步是先选项目，不开始认证流程。

## 官方依据

- [Codex MCP配置](https://developers.openai.com/codex/mcp)：环境变量引用、工具过滤及认证方式。
- [GitHub MCP Codex安装](https://github.com/github/github-mcp-server/blob/main/docs/installation-guides/install-codex.md)：Remote地址及PAT引用方式。
- [GitHub REST排错](https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api)：私有资源404、403/429与授权范围。
- [GitHub Token管理与限制](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)：最小权限、资源所有者及协作者限制。
