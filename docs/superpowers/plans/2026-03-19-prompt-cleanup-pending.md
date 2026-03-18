# Prompt 结构清理（待梳理）

> **状态：** 待确认后执行
> **来源：** 2026-03-19 提示词分析，修复 #5

---

## 背景

当前 4 个 SKILL.md 文件（task-planner-skill、task-executor-skill、task-reviewer-skill、task-patrol-skill）各自有一个简版的「工作流程」章节，与对应 `prompts/templates/` 中的详细唤醒流程形成重复。

两者分工：
- `prompts/templates/*.md` = Agent System Prompt，定义角色身份 + 完整唤醒操作流程（权威版）
- `skills/task-*-skill/SKILL.md` = 工具命令参考手册

问题：SKILL.md 的「工作流程」节是 templates 中详细流程的简化版，未来任意一边更新都会造成不一致。

---

## 待执行任务

- [ ] **Task 1: 删除 4 个 SKILL.md 的「工作流程」章节，添加指向角色提示词的注释**

  涉及文件：
  - `skills/task-planner-skill/SKILL.md`（第 14-16 行）
  - `skills/task-executor-skill/SKILL.md`（对应「工作流程」节）
  - `skills/task-reviewer-skill/SKILL.md`（对应「工作流程」节）
  - `skills/task-patrol-skill/SKILL.md`（对应「工作流程」节）

  每个文件的变更：
  1. 删除「## 工作流程」及其箭头流程一行
  2. 在文件顶部（`## 认证信息` 之前）添加：
     ```markdown
     > 详细唤醒流程见角色提示词（System Prompt）。本文件仅包含命令参考。
     ```

- [ ] **Task 2: 确认 templates 与 SKILL.md 的命令示例一致性**

  检查以下内容在两个文件中是否一致：
  - `log create` 的 action 类型（coding/delivery/blocked/reflection/plan/review/patrol）
  - `st` 命令参数格式（`--session`、`--assign` 等）
  - 分页参数 `--page` / `--page-size` 是否都有提及

  有差异的地方以 SKILL.md 为准（命令参考更精确），同步更新 templates。

---

## 预期收益

- 减少维护两处的负担
- 新 Agent 配置时看 SKILL.md 只需关注命令，看 templates 只需关注流程
- 未来修改唤醒流程只改 templates 一处即可
