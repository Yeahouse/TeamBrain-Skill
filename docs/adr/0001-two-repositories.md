# ADR 0001：Skill 与测试数据分仓

日期：2026-10-21
状态：用户已确认

本地父目录：D:\SJUT Course\智能系统\skill开发\TeamBrainSkill

- teambrain-skill 对应 Yeahouse/TeamBrain-Skill：Skill 开发及后续分发。
- teambrain-poc-test 对应 Yeahouse/teambrain-test：自己的开发测试数据。
- 不使用 Yeahouse/TeamBrainSkill，不修改现有其他项目。
- 已有远程仓库保持当前可见性，新建远程仓库使用 Private。

普通用户将工作记录保存到自己的团队仓库，不写入本开发测试仓库。两个本地仓库互不嵌套，分别提交和推送。
