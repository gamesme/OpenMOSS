# 代码审查待办项（Backlog）

> **状态：** 暂不修复，系统可正常运行
> **来源：** 2026-03-19 全量代码审查
> **优先级：** Critical > Important > Minor

---

## Critical — 最优先修复

- [ ] **C1: 路由顺序 bug — `/scores/me/logs` 被 `/{agent_id}` 覆盖**
  - 文件：`app/routers/scores.py`
  - 问题：`GET /me/logs` 注册在 `GET /{agent_id}` 之后，Agent 调用 `/scores/me/logs` 会命中 `/{agent_id}` 返回 403
  - 修复：将 `/me` 和 `/me/logs` 路由移到 `/{agent_id}` 之前注册

- [ ] **C2: Admin token 无限增长 + 永不过期**
  - 文件：`app/routers/admin.py`
  - 问题：`_admin_tokens` 集合只增不减，token 永不失效，内存泄漏且无法踢出已登录会话
  - 修复：改为 `{token: expire_time}` 字典 + 设 TTL（如 24 小时）+ 登录时清理过期 token

- [ ] **C3: 注册令牌比较存在计时侧信道**
  - 文件：`app/routers/agents.py`（注册 endpoint 处的 `!=` 比较）
  - 问题：Python 字符串 `!=` 非常数时间，攻击者可逐字符猜测 token
  - 修复：`import secrets` 后改为 `not secrets.compare_digest(x_registration_token, config.registration_token)`

---

## Important — 建议修复

- [ ] **I1: SQLite 未开启 WAL 模式**
  - 文件：`app/database.py`
  - 问题：调度器后台线程与 API 请求并发写入时会出现 `database is locked`，调度任务静默失败
  - 修复：engine 创建后执行 `with engine.connect() as conn: conn.execute(text("PRAGMA journal_mode=WAL"))`

- [ ] **I2: sub-task 的 priority / type 字段无枚举校验**
  - 文件：`app/services/sub_task_service.py`
  - 问题：`priority`（high/medium/low）和 `type`（once/recurring）未校验，任意字符串可写入
  - 修复：在 Pydantic schema 或 service 层加枚举校验

- [ ] **I3: `start_sub_task` 绕过 VALID_TRANSITIONS 状态机**
  - 文件：`app/services/sub_task_service.py`
  - 问题：函数内手动检查状态而非走 `_change_status`，未来状态机变更不会自动反映
  - 修复：重构为通过 `_change_status` 驱动，或至少加注释说明为何绕过

- [ ] **I5: CORS 配置违反规范**
  - 文件：`app/main.py`
  - 问题：`allow_origins=["*"]` + `allow_credentials=True` 违反 CORS 规范，浏览器会拒绝凭证请求
  - 修复：将 `allow_origins` 改为具体来源（如 `["http://localhost:6565", "http://localhost:5173"]`）

- [ ] **I6: 启动时注册令牌打印到日志**
  - 文件：`app/main.py`（lifespan 中的 `print` 语句）
  - 问题：`registration_token` 明文写入 `logs/stdout.log`，任何能读日志的人都能注册 Agent
  - 修复：删除该 print，或改为仅在首次初始化时打印一次

- [ ] **I7: Docker healthcheck 不检查 HTTP 状态码**
  - 文件：`docker-compose.yml`
  - 问题：`httpx.get()` 不 raise on 4xx/5xx，服务返回 500 也会被判为健康
  - 修复：改为 `httpx.get('http://localhost:6565/api/health').raise_for_status()`

---

## Minor — 低优先级

- [ ] **M2: config.py 首次启动会重写 YAML 文件**
  - 文件：`app/config.py`（`_auto_encrypt_password`）
  - 问题：`yaml.dump` 重写会丢失注释、重排键名
  - 修复：用 `ruamel.yaml` 保留注释，或仅替换 password 字段所在行

- [ ] **M3: `get_safe_config` 仍暴露 registration_token**
  - 文件：`app/config.py`
  - 问题：方法名暗示「安全」但仍返回敏感 token，有误导性
  - 修复：加注释说明设计意图（admin 可查看），或改名为 `get_admin_config`

- [ ] **M5: SetupView 注册令牌建议值用 `Math.random()` 生成**
  - 文件：`webui/src/views/SetupView.vue`（`generateToken()` 函数）
  - 问题：`Math.random()` 不是密码学安全随机数
  - 修复：改用 `crypto.getRandomValues(new Uint8Array(32))` 转 hex

- [ ] **M7: Makefile start 防重复启动守卫无效**
  - 文件：`Makefile`（`start` target）
  - 问题：`exit 0` 在 Make 子 shell 里只退出当前行，后续命令仍会执行，会出现双启动
  - 修复：改为 `if [ -f $(SOCK) ]; then echo "已在运行"; else .venv/bin/supervisord -c $(CONF); fi`

- [ ] **M8: Dockerfile 未拷贝 `rules/` 目录**
  - 文件：`Dockerfile`
  - 问题：容器启动时 `rules/global-rule-example.md` 不存在，全局规则静默加载失败
  - 修复：添加 `COPY rules/ ./rules/`
