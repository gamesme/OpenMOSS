"""
后台调度器 — 超时自动 block + recurring 子任务自动续建
"""
import uuid
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import config
from app.database import SessionLocal
from app.models.sub_task import SubTask
from app.models.task import Task


def _check_timeouts():
    """
    Job 1: 扫描超时子任务，自动标记为 blocked。
    - assigned 超过 assigned_timeout_hours 未 start
    - in_progress 超过 in_progress_timeout_hours 未 submit
    - rework 超过 rework_timeout_hours 未 start
    """
    db = SessionLocal()
    try:
        now = datetime.now()
        blocked_count = 0

        # assigned 超时
        cutoff = now - timedelta(hours=config.assigned_timeout_hours)
        stale = db.query(SubTask).filter(
            SubTask.status == "assigned",
            SubTask.updated_at < cutoff,
        ).all()
        for st in stale:
            st.status = "blocked"
            st.current_session_id = None
            blocked_count += 1

        # in_progress 超时
        cutoff = now - timedelta(hours=config.in_progress_timeout_hours)
        stale = db.query(SubTask).filter(
            SubTask.status == "in_progress",
            SubTask.updated_at < cutoff,
        ).all()
        for st in stale:
            st.status = "blocked"
            st.current_session_id = None
            blocked_count += 1

        # rework 超时
        cutoff = now - timedelta(hours=config.rework_timeout_hours)
        stale = db.query(SubTask).filter(
            SubTask.status == "rework",
            SubTask.updated_at < cutoff,
        ).all()
        for st in stale:
            st.status = "blocked"
            st.current_session_id = None
            blocked_count += 1

        if blocked_count > 0:
            db.commit()
            print(f"[Scheduler] 超时巡查：已自动 blocked {blocked_count} 个子任务")
    except Exception as e:
        db.rollback()
        print(f"[Scheduler] 超时巡查异常: {e}")
    finally:
        db.close()


def _renew_recurring_sub_tasks():
    """
    Job 2: 扫描已完成的 recurring 子任务，自动创建同名新子任务开启下一轮。
    只续建所属 Task 仍为 active/in_progress 的子任务。
    """
    db = SessionLocal()
    try:
        renewed_count = 0

        done_recurring = db.query(SubTask).filter(
            SubTask.type == "recurring",
            SubTask.status == "done",
        ).all()

        for st in done_recurring:
            # 检查父任务是否仍活跃
            task = db.query(Task).filter(Task.id == st.task_id).first()
            if not task or task.status not in ("active", "in_progress"):
                continue

            # 检查是否已存在同名 pending/assigned 子任务（避免重复续建）
            existing = db.query(SubTask).filter(
                SubTask.task_id == st.task_id,
                SubTask.name == st.name,
                SubTask.status.in_(("pending", "assigned", "in_progress", "review", "rework")),
            ).first()
            if existing:
                continue

            # 创建新一轮子任务
            new_st = SubTask(
                id=str(uuid.uuid4()),
                task_id=st.task_id,
                module_id=st.module_id,
                name=st.name,
                description=st.description,
                deliverable=st.deliverable,
                acceptance=st.acceptance,
                type="recurring",
                status="pending",
                priority=st.priority,
            )
            db.add(new_st)
            renewed_count += 1

        if renewed_count > 0:
            db.commit()
            print(f"[Scheduler] recurring 续建：已创建 {renewed_count} 个新子任务")
    except Exception as e:
        db.rollback()
        print(f"[Scheduler] recurring 续建异常: {e}")
    finally:
        db.close()


def create_scheduler() -> BackgroundScheduler:
    """创建并配置调度器，返回未启动的实例"""
    scheduler = BackgroundScheduler(timezone="Asia/Shanghai")

    scheduler.add_job(
        _check_timeouts,
        trigger="interval",
        minutes=config.timeout_check_interval,
        id="timeout_check",
        name="超时子任务自动 blocked",
        max_instances=1,        # 防止上一次未完成时重叠执行
        coalesce=True,          # 错过的触发点合并为一次
    )

    scheduler.add_job(
        _renew_recurring_sub_tasks,
        trigger="interval",
        minutes=config.recurring_check_interval,
        id="recurring_renew",
        name="recurring 子任务自动续建",
        max_instances=1,
        coalesce=True,
    )

    return scheduler
