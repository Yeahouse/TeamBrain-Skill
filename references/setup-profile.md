# 每位用户的本地项目与成员配置

默认位置仍为当前系统用户目录/.config/teambrain/profile.json。Windows从USERPROFILE解析，其他系统用当前用户主目录。不同操作系统用户各自保存；多人共用系统用户时不要假定本地署名属于当前人。该位置是TeamBrain约定，不是Codex内置配置。

## 兼容结构

继续使用version=1，无需迁移旧单项目配置。projects以owner/repo为稳定键，同一个仓库大小写变体不重复添加；可选name允许用户可读名称，旧配置没有name时展示仓库标识。

```json
{
  "version": 1,
  "active_project": "owner/repository",
  "projects": {
    "owner/repository": {
      "name": "用户确认的项目名称",
      "branch": "main",
      "repository_confirmed": true,
      "member": {
        "display_name": "该项目中本人确认的署名",
        "confirmed": true,
        "role": "可选角色"
      },
      "preferred_connection": "已有连接名称"
    }
  }
}
```

repository_confirmed表示用户确认本地绑定，不证明GitHub可读或可写。member.confirmed仅表示项目署名确认，不证明GitHub登录身份。active_project是保存的默认候选，不是跨会话的当前工作授权。preferred_connection不创建服务器或保证凭据有效。远端权限每次基于工具/响应判断，不保存“永久可写”。禁止保存Token、认证头、密码或私钥；未知安全字段原样保留，不向模型打印整个原始profile。

## 唯一读写入口

使用现有`scripts/read-profile.py`，不手工拼接JSON覆盖profile。脚本路径相对于Skill安装目录，不是用户项目工作目录；在其他目录工作时从实际Skill入口定位脚本，使用其完整路径，不复制一份到项目中。下例中的owner/repository只是占位说明：

```text
python scripts/read-profile.py list
python scripts/read-profile.py resolve --explicit owner/repository
python scripts/read-profile.py resolve --session owner/repository --require-member
python scripts/read-profile.py resolve --use-saved
python scripts/read-profile.py preview add --project owner/repository --name 项目名称 --branch main
python scripts/read-profile.py preview switch --project owner/repository
python scripts/read-profile.py preview member --project owner/repository --member 署名 --role 研究
python scripts/read-profile.py apply --plan 临时预览文件 --confirm 该预览的确认摘要
```

默认无子命令仍返回旧版active候选字段，兼容旧调用；项目管理用list，实际任务统一用resolve。resolve只接受本次明确目标、会话已确认目标，或用户明确恢复默认项目；不要从list的saved_active_project自动填--session。

预览结构化输出供AI转换为简短自然语言，不把内部摘要/JSON作为普通用户流程。确认摘要是内容锁，不是用户授权来源。未获得针对该预览的明确同意就不得apply；修改署名、绑定或保存默认项目都要先展示变化。只读查询和临时指定目标不自动保存配置。

## 保存和权限

apply在本地检查原文件指纹，保存前生成同目录唯一.bak并验证字节；只修改选中项目或active_project，保留其他项目及安全未知字段，校验临时文件后原子替换。已有文件的Windows DACL/POSIX权限会保留，避免丢失之前授权的单文件读取权限；脚本不会自行给沙箱组新增权限。没有schema升级，也不自动迁移或删除旧数据。备份与临时文件不进入共享Git仓库。

真实profile首次创建后，正常Codex沙箱是否可读需单独实测。遇Access denied不将其当作不存在，不能借更换USERPROFILE、关闭沙箱或特殊测试路径证明默认配置已恢复；最小授权变更须用户另行批准。不得用默认错误处理的Test-Path假值判断缺文件。

明确的`--profile`参数允许用户指定另一份本地文件或隔离测试配置；它不更改默认路径。此类测试只能证明替代路径行为，不能冒充真实默认profile的跨会话验收。真实个人配置变更须单独预览并取得用户授权。
