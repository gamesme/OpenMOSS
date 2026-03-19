# Agent 首次注册指南

> 本文档指导 OpenClaw Agent 完成首次注册，获取 API Key 并自动写入 SKILL.md。
> 每个 Agent 只需执行一次。**完成后本文件会自动删除。**

---

## 前置条件

- 任务调度服务已启动（`http://localhost:6565`）
- 你有注册令牌（Registration Token），由管理员提供
- 你已知道自己的角色：`planner` / `executor` / `reviewer` / `patrol`

---

## 注册步骤

### 第 1 步：注册自己，获取 API Key

在你的 Skill 目录下运行：

```bash
python task-cli.py register --name "你的中文名称" --role <你的角色> --token <注册令牌> --description "你的专业能力描述"
```

> ⚠️ **请使用自己的中文名注册**（如"AI小吴"、"AI酱瓜"），方便团队成员识别和协作。

示例：

```bash
python task-cli.py register --name "AI小吴" --role executor --token openclaw-register-2024 --description "专业资讯搜集员，擅长中文互联网信息检索"
```

注册成功后，终端会输出：

```
✅ 注册成功
   Agent ID:  a1b2c3d4-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   API Key:   ock_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   角色:      executor
```

**记住这个 API Key，下一步要用。**

---

### 第 2 步：自动初始化（API Key 写入 + SKILL.md 更新）

用第 1 步得到的 API Key 运行 `update` 命令，通过 `--skill-dir` 指定正确的 Skill 目录：

```bash
python task-cli.py --key <你的API_KEY> update --skill-dir skills/<你的角色>-skill
```

示例（executor 角色）：

```bash
python task-cli.py --key ock_xxx update --skill-dir skills/task-executor-skill
```

角色对应目录：
- `planner` → `skills/task-planner-skill`
- `executor` → `skills/task-executor-skill`
- `reviewer` → `skills/task-reviewer-skill`
- `patrol` → `skills/task-patrol-skill`

这一步会自动完成：
- ✅ 将最新 task-cli.py 写入指定 Skill 目录
- ✅ 将 API Key 已填入的 SKILL.md 写入指定 Skill 目录

---

### 第 3 步：验证注册成功

使用已写入 Skill 目录的 CLI 验证：

```bash
python skills/<你的角色>-skill/task-cli.py --key <你的API_KEY> rules
```

如果返回规则内容，说明注册成功且 Key 有效。后续直接使用 Skill 目录下的 `task-cli.py`。

---

## 之后的使用

注册完成后，每次执行命令时带上你的 Key（已写入 SKILL.md，参考其中的认证信息）：

```bash
python task-cli.py --key <你的API_KEY> <命令> [参数]
```

后续如需更新 CLI 或 SKILL.md：

```bash
python skills/<你的角色>-skill/task-cli.py --key <你的API_KEY> update --skill-dir skills/<你的角色>-skill
```

---

## 常见问题

| 问题               | 解决方案                                                |
| ------------------ | ------------------------------------------------------- |
| 注册令牌无效       | 联系管理员确认令牌是否正确，检查 config.yaml 中的 `agent.registration_token` |
| API Key 丢失       | 联系管理员通过 WebUI 或 `POST /admin/agents/{id}/reset-key` 重置 |
| 注册时提示名称重复 | 更换一个唯一的名称                                      |
| `update` 后 SKILL.md 里 API Key 还是空 | 检查 `update` 是否返回 200；确认服务已启动且 Key 有效 |
