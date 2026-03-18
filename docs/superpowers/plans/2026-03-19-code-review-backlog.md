# 代码审查待办项（Backlog）

> **状态：** ✅ 已全部修复（2026-03-19）
> **来源：** 2026-03-19 全量代码审查
> **优先级：** Critical > Important > Minor

---

## Critical — 最优先修复

- [x] **C1: 路由顺序 bug — `/scores/me/logs` 被 `/{agent_id}` 覆盖**
  - 文件：`app/routers/scores.py`
  - 修复：将 `/{agent_id}` 路由移到 `/me/logs` 之后注册

- [x] **C2: Admin token 无限增长 + 永不过期**
  - 文件：`app/routers/admin.py`
  - 修复：改为 `{token: expire_time}` 字典 + 24 小时 TTL + 登录时清理过期 token

- [x] **C3: 注册令牌比较存在计时侧信道**
  - 文件：`app/routers/agents.py`
  - 修复：改为 `secrets.compare_digest()`

---

## Important — 建议修复

- [x] **I1: SQLite 未开启 WAL 模式**
  - 文件：`app/database.py`
  - 修复：engine 创建后执行 `PRAGMA journal_mode=WAL`

- [x] **I2: sub-task 的 priority / type 字段无枚举校验**
  - 文件：`app/services/sub_task_service.py`
  - 修复：`create_sub_task` 和 `update_sub_task` 加枚举校验

- [x] **I3: `start_sub_task` 绕过 VALID_TRANSITIONS 状态机**
  - 文件：`app/services/sub_task_service.py`
  - 修复：重构为通过 `_change_status` 驱动

- [x] **I5: CORS 配置违反规范**
  - 文件：`app/main.py`
  - 修复：`allow_origins` 改为具体来源列表（localhost + 配置的外网地址）

- [x] **I6: 启动时注册令牌打印到日志**
  - 文件：`app/main.py`
  - 修复：删除 registration_token 的 print 语句

- [x] **I7: Docker healthcheck 不检查 HTTP 状态码**
  - 文件：`docker-compose.yml`
  - 修复：改为 `.raise_for_status()`

---

## Minor — 低优先级

- [x] **M2: config.py 首次启动会重写 YAML 文件**
  - 文件：`app/config.py`（`_auto_encrypt_password`）
  - 修复：改为 regex 定向替换 password 行，保留注释和键名顺序

- [x] **M3: `get_safe_config` 仍暴露 registration_token**
  - 文件：`app/config.py`
  - 修复：重命名为 `get_admin_config`，更新 docstring 说明设计意图

- [x] **M5: SetupView 注册令牌建议值用 `Math.random()` 生成**
  - 文件：`webui/src/views/SetupView.vue`（`generateToken()` 函数）
  - 修复：改用 `crypto.getRandomValues(new Uint8Array(16))` 转 hex

- [x] **M7: Makefile start 防重复启动守卫无效**
  - 文件：`Makefile`（`start` target）
  - 修复：改为 `if [ -f $(SOCK) ]; then ...; else ...; fi` 结构

- [x] **M8: Dockerfile 未拷贝 `rules/` 目录**
  - 文件：`Dockerfile`
  - 修复：添加 `COPY rules/ ./rules/`
