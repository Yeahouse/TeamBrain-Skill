# 每位用户的本地项目与成员配置

可选路径：当前系统用户目录/.config/teambrain/profile.json。每位成员使用自己的操作系统用户目录；多人共用同一系统账号时，先询问本次成员身份，不假定本地配置属于当前人。

示例仅说明结构，不是已配置或已获授权的证据：

```json
{
  "version": 1,
  "active_project": "owner/repo",
  "projects": {
    "owner/repo": {
      "branch": "main",
      "repository_confirmed": true,
      "member": {
        "display_name": "用户明确确认的署名",
        "confirmed": true
      },
      "preferred_connection": "已存在的连接名称"
    }
  }
}
```

缺少member不影响只读查询；member.confirmed不是GitHub认证标志。preferred_connection只表示选择哪个既有连接，不创建服务器、不承诺其凭据有效。只读/写入权限每次根据真实工具及服务器响应判断，不持久保存“永久可写”。

仅通过已有本地文件工具读写，先验证JSON、version和选中项目。只向模型展示仓库、分支、已确认标志与成员署名等必要字段；如果文件意外含凭据，不打印原文、不上传，而是提示用户处理。不得从测试记录或Git提交作者填充正式成员名。

没有用户确认就不创建配置文件。损坏或不认识的格式先提示，不自动清空重建。修改只影响用户选中的项目键，保留其他项目。profile不纳入Git，不修改项目远端结构。

## 可靠读取与访问拒绝

优先运行 Skill 自带的 `scripts/read-profile.py`，只输出当前项目已确认的必要字段。Windows 使用进程继承的 USERPROFILE，其他系统使用当前用户主目录；不把 ~ 当作未展开的字面目录。此路径是TeamBrain本地约定，不是Codex官方内置配置位置。

`ok` 时复用已确认仓库、分支与署名，不要求用户再次填写；本次用户明确覆盖时以用户指令为准。`not_found` 才表示文件不存在；`access_denied` 表示不可读取，不能宣称不存在或自动创建替代配置。其他读取错误、损坏JSON、未知版本或未确认绑定分别报告，不清空原文件。

不要用默认错误处理的 Test-Path 假值判定文件不存在：PowerShell拒绝访问可以是非终止错误，随后仍进入else分支。使用上述读取器，或直接读取并以ErrorAction Stop捕获具体异常。不能通过修改测试Prompt注入配置来冒充复用。

Windows legacy elevated沙箱使用专用低权限身份；如真实ACL证据表明个人文件不可读，可经用户授权仅向已有Codex沙箱组授予该profile.json文件读取。不得授予写入、父目录内容列举、继承到其他文件或改为Full Access；不自动修改ACL。替换文件后需检查是否仍保留该单文件读取授权。其他系统/后端需依据其实际权限诊断。
