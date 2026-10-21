# 初学者操作指南

Git 是本地版本记录工具，GitHub 是远端备份；commit 只保存本地，push 才上传。两个仓库分别操作。

## 登录与首次备份

1. 完成 GitHub 登录授权。推荐安装 GitHub CLI 后运行 `gh auth login`，选择 GitHub.com、HTTPS、浏览器授权；不要把令牌发到聊天里。
2. 用 `gh api user --jq .login` 确认是 Yeahouse。用 `gh repo view Yeahouse/TeamBrain-Skill` 和 `gh repo view Yeahouse/teambrain-test` 核对仓库。
3. 已存在：克隆远端到对应本地子目录，再加入准备好的文件，不覆盖已有文件。不存在：本地初始化后，以 `gh repo create` 创建私有远端。权限错误不能当作仓库不存在。
4. 在每个仓库查看 `git status`，逐一检查文件，暂存本次文件后执行 `git commit -m "Initialize TeamBrain R8 workspace"`，再推送当前分支。
5. 用 `git rev-parse HEAD` 与 `git ls-remote origin` 对比相应分支的提交 SHA，并回读远端文件。推送报错时先查远端，不盲目重复或强推。

这些是后续操作说明，不代表上述步骤已经执行。登录、远端读取及合并均需按当时真实状态选择操作。

## 日常开发

开始前查看远端更新；改动后检查差异，提交有意义的一小步，再推送。Skill 规则写入源码仓库；实验记录和附件写入测试仓库。遇到冲突先保留两边内容并核对，禁止用强推解决普通冲突。
