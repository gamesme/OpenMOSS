"""
提示词管理业务逻辑 — 文件扫描、frontmatter 解析、Prompt 组合
"""
import re
from pathlib import Path
from datetime import date
from typing import Optional

import frontmatter

from app.config import config

# ── 目录常量 ────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[2]  # app/services → app → 项目根目录
TEMPLATES_DIR = BASE_DIR / "prompts" / "templates"
AGENTS_DIR = BASE_DIR / "prompts" / "agents"

# ── 合法角色列表 ────────────────────────────────────────
VALID_ROLES = {"planner", "executor", "reviewer", "patrol"}

# ── 系统垃圾文件过滤 ───────────────────────────────────
IGNORED_FILES = {".DS_Store", "Thumbs.db", "desktop.ini", ".gitkeep"}

# ── 文件名校验（只允许小写英文、数字、短横线） ──────────
SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9\-]*$")


# ======================================================================
#  工具函数
# ======================================================================

def _is_valid_md(path: Path) -> bool:
    """判断是否为合法的 .md 文件（排除垃圾文件和非 .md）"""
    return (
        path.is_file()
        and path.suffix == ".md"
        and path.name not in IGNORED_FILES
    )


def _parse_prompt_file(path: Path) -> dict:
    """解析单个提示词文件，返回元数据 + 内容"""
    post = frontmatter.load(str(path))
    slug = path.stem  # 文件名去掉 .md

    # 从 frontmatter 取元数据，缺失则标记
    meta = {
        "slug": slug,
        "filename": path.name,
        "name": post.get("name", ""),
        "role": post.get("role", ""),
        "description": post.get("description", ""),
        "created_at": str(post.get("created_at", "")),
        "example": bool(post.get("example", False)),
        "content": post.content,
        "has_frontmatter": bool(post.metadata),
    }

    # 诊断状态
    if not post.metadata:
        meta["status"] = "unconfigured"  # 无 frontmatter
    elif meta["role"] and not slug.startswith(meta["role"] + "-"):
        meta["status"] = "rename_suggested"  # 命名不规范
    else:
        meta["status"] = "ok"

    return meta


def _validate_slug(slug: str) -> Optional[str]:
    """校验 slug 合法性，返回错误信息或 None"""
    if not slug:
        return "slug 不能为空"
    if not SLUG_PATTERN.match(slug):
        return "slug 只允许小写英文、数字和短横线，且不能以短横线开头"
    return None


# ======================================================================
#  模板 CRUD
# ======================================================================

def list_templates() -> list[dict]:
    """列出所有角色模板"""
    if not TEMPLATES_DIR.exists():
        return []

    result = []
    for path in sorted(TEMPLATES_DIR.iterdir()):
        if path.is_dir() and not path.name.startswith('.'):
            # New subdirectory format: executor/, planner/, etc.
            role = path.name
            soul_path = path / "SOUL.md"
            agents_path = path / "AGENTS.md"
            soul = soul_path.read_text(encoding="utf-8") if soul_path.exists() else ""
            agents = agents_path.read_text(encoding="utf-8") if agents_path.exists() else ""
            content = "\n\n---\n\n".join(filter(None, [soul.strip(), agents.strip()]))
            result.append({
                "role": role,
                "filename": f"{role}/",
                "content": content,
                "soul": soul,
                "agents": agents,
            })
        elif _is_valid_md(path):
            # Legacy flat file format
            role = path.stem
            if role.startswith("task-"):
                role = role[5:]
            content = path.read_text(encoding="utf-8")
            result.append({
                "role": role,
                "filename": path.name,
                "content": content,
            })
    return result


def get_template(role: str) -> Optional[dict]:
    """获取指定角色模板（支持子目录格式和旧版平铺文件格式）"""
    # New: subdirectory format
    subdir = TEMPLATES_DIR / role
    if subdir.is_dir():
        soul_path = subdir / "SOUL.md"
        agents_path = subdir / "AGENTS.md"
        soul = soul_path.read_text(encoding="utf-8") if soul_path.exists() else ""
        agents = agents_path.read_text(encoding="utf-8") if agents_path.exists() else ""
        content = "\n\n---\n\n".join(filter(None, [soul.strip(), agents.strip()]))
        return {
            "role": role,
            "filename": f"{role}/",
            "content": content,
            "soul": soul,
            "agents": agents,
        }

    # Legacy: flat file format
    path = TEMPLATES_DIR / f"{role}.md"
    if not path.exists():
        path = TEMPLATES_DIR / f"task-{role}.md"
    if not path.exists():
        return None
    return {
        "role": role,
        "filename": path.name,
        "content": path.read_text(encoding="utf-8"),
    }


def update_template(role: str, content: str, layer: Optional[str] = None) -> dict:
    """更新角色模板内容"""
    if role not in VALID_ROLES:
        raise ValueError(f"无效角色 '{role}'，可选: {', '.join(VALID_ROLES)}")

    subdir = TEMPLATES_DIR / role
    if subdir.is_dir():
        # New subdirectory format
        if layer == "soul":
            subdir.mkdir(parents=True, exist_ok=True)
            (subdir / "SOUL.md").write_text(content, encoding="utf-8")
            return {"role": role, "filename": f"{role}/SOUL.md"}
        elif layer == "agents":
            subdir.mkdir(parents=True, exist_ok=True)
            (subdir / "AGENTS.md").write_text(content, encoding="utf-8")
            return {"role": role, "filename": f"{role}/AGENTS.md"}
        else:
            # Write full combined content — split at separator
            parts = content.split("\n\n---\n\n", 1)
            subdir.mkdir(parents=True, exist_ok=True)
            (subdir / "SOUL.md").write_text(parts[0].strip(), encoding="utf-8")
            (subdir / "AGENTS.md").write_text(parts[1].strip() if len(parts) > 1 else "", encoding="utf-8")
            return {"role": role, "filename": f"{role}/"}
    else:
        # Legacy flat file format
        TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        path = TEMPLATES_DIR / f"{role}.md"
        path.write_text(content, encoding="utf-8")
        return {"role": role, "filename": path.name}


# ======================================================================
#  Agent 提示词 CRUD
# ======================================================================

def list_agents() -> list[dict]:
    """列出所有 Agent 提示词（扫描 prompts/agents/ 目录）"""
    if not AGENTS_DIR.exists():
        return []

    result = []
    for path in sorted(AGENTS_DIR.iterdir()):
        if not _is_valid_md(path):
            continue
        try:
            meta = _parse_prompt_file(path)
            # 列表不返回完整内容，节省带宽
            meta.pop("content", None)
            result.append(meta)
        except Exception:
            # 解析失败的文件跳过
            continue
    return result


def get_agent(slug: str) -> Optional[dict]:
    """获取 Agent 提示词详情"""
    path = AGENTS_DIR / f"{slug}.md"
    if not path.exists():
        return None
    return _parse_prompt_file(path)


def create_agent(
    slug: str,
    name: str,
    role: str,
    description: str,
    content: str,
) -> dict:
    """新建 Agent 提示词"""
    # 校验 role
    if role not in VALID_ROLES:
        raise ValueError(f"无效角色 '{role}'，可选: {', '.join(VALID_ROLES)}")

    # 拼接完整 slug: {role}-{slug}
    full_slug = f"{role}-{slug}" if not slug.startswith(role + "-") else slug

    # 校验 slug
    err = _validate_slug(full_slug)
    if err:
        raise ValueError(err)

    # 检查唯一性
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    path = AGENTS_DIR / f"{full_slug}.md"
    if path.exists():
        raise ValueError(f"文件 '{full_slug}.md' 已存在，请更换名称")

    # 组装 frontmatter + 内容
    post = frontmatter.Post(content)
    post["name"] = name
    post["role"] = role
    post["description"] = description
    post["created_at"] = str(date.today())

    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    return {"slug": full_slug, "filename": path.name}


def update_agent(
    slug: str,
    name: Optional[str] = None,
    role: Optional[str] = None,
    description: Optional[str] = None,
    content: Optional[str] = None,
) -> dict:
    """编辑 Agent 提示词（支持重命名）"""
    path = AGENTS_DIR / f"{slug}.md"
    if not path.exists():
        raise ValueError(f"文件 '{slug}.md' 不存在")

    post = frontmatter.load(str(path))

    # 更新字段
    if name is not None:
        post["name"] = name
    if role is not None:
        if role not in VALID_ROLES:
            raise ValueError(f"无效角色 '{role}'，可选: {', '.join(VALID_ROLES)}")
        post["role"] = role
    if description is not None:
        post["description"] = description
    if content is not None:
        post.content = content

    # 确保 created_at 存在
    if "created_at" not in post.metadata:
        post["created_at"] = str(date.today())

    new_role = post.get("role", "")
    new_slug = slug

    # 如果 role 变了或文件名不规范，自动重命名
    if new_role and not slug.startswith(new_role + "-"):
        # 去掉旧的 role 前缀（如果有）
        base_name = slug
        for r in VALID_ROLES:
            if slug.startswith(r + "-"):
                base_name = slug[len(r) + 1:]
                break
        new_slug = f"{new_role}-{base_name}"

        new_path = AGENTS_DIR / f"{new_slug}.md"
        if new_path.exists() and new_path != path:
            raise ValueError(f"重命名目标 '{new_slug}.md' 已存在")

        # 写入新文件，删除旧文件
        new_path.write_text(frontmatter.dumps(post), encoding="utf-8")
        if new_path != path:
            path.unlink()
    else:
        path.write_text(frontmatter.dumps(post), encoding="utf-8")

    return {"slug": new_slug, "filename": f"{new_slug}.md"}


def delete_agent(slug: str) -> bool:
    """删除 Agent 提示词"""
    path = AGENTS_DIR / f"{slug}.md"
    if not path.exists():
        raise ValueError(f"文件 '{slug}.md' 不存在")
    path.unlink()
    return True


# ======================================================================
#  Prompt 组合（一键复制用）
# ======================================================================

def compose_prompt(slug: str) -> str:
    """
    生成完整 Prompt。
    新格式：内容已包含模板和对接指引，直接返回。
    旧格式：拼接模板 + Agent 内容 + 自动生成的对接指引。
    """
    agent_data = get_agent(slug)
    if not agent_data:
        raise ValueError(f"Agent 提示词 '{slug}' 不存在")

    role = agent_data.get("role", "")
    agent_content = agent_data.get("content", "")

    # 新格式：内容已包含对接指引
    if ONBOARDING_MARKER in agent_content:
        return agent_content.strip()

    # 旧格式：拼接模板 + Agent 内容 + 对接指引
    template_content = ""
    if role:
        template = get_template(role)
        if template:
            template_content = template["content"]

    parts = []
    if template_content:
        parts.append(template_content.strip())
    if agent_content:
        parts.append(agent_content.strip())
    parts.append(generate_onboarding(role))

    return "\n\n---\n\n".join(parts)


ONBOARDING_MARKER = "## 🔧 平台对接"


def generate_onboarding(role: str = "") -> str:
    """生成平台对接指引文本（变量从 config 自动填充）"""
    external_url = config.server_external_url
    registration_token = config.registration_token
    skill_dir = f"skills/task-{role}-skill" if role else "skills/task-<role>-skill"
    bs = "\\"

    lines = [
        "## 🔧 平台对接（仅用于首次注册，完成后请删除本段）",
        "",
        "> ⚠️ **重要提示**：以下内容仅用于首次注册，注册完成后务必从系统提示词中移除本段。",
        "> 请勿将本段写入 AGENTS.md、SOUL.md 或任何长期使用的系统提示词中。",
        "",
        "### 第一步：注册到任务系统（如已注册可跳过）",
        "",
        "```bash",
        f'python task-cli.py register --name "你的名字" --role {role or "<role>"} {bs}',
        f'  --token "{registration_token}" --description "你的专业能力描述"',
        "```",
        "",
        "→ 返回你的 API Key，后续所有操作需要携带",
        "",
        "### 第二步：自动初始化（API Key 写入 + SKILL.md 更新）",
        "",
        "```bash",
        f"python task-cli.py --key <你的API_KEY> update --skill-dir {skill_dir}",
        "```",
        "",
        "这一步会自动完成：",
        "- ✅ 将最新 task-cli.py 写入指定 Skill 目录",
        "- ✅ 将 API Key 已填入的 SKILL.md 写入指定 Skill 目录",
        "",
        "### 第三步：验证注册成功",
        "",
        "```bash",
        f"python {skill_dir}/task-cli.py --key <你的API_KEY> rules",
        "```",
        "",
        "如果返回规则内容，说明注册成功且 Key 有效。",
        "",
        "### 连接信息",
        f"- 服务地址: {external_url}",
        f"- 注册令牌: {registration_token}",
    ]
    return "\n".join(lines)
