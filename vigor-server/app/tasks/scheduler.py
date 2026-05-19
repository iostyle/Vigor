from app.celery_app import celery_app
from app.database import SessionLocal
from app.services.scheduled_tasks import run_due_scheduled_tasks


@celery_app.task(
    name="app.tasks.scheduler.run_scheduled_tasks",
    queue="updater",
)
def run_scheduled_tasks():
    db = SessionLocal()
    try:
        dispatched = run_due_scheduled_tasks(db)
        return {"status": "success", "dispatched": dispatched}
    finally:
        db.close()
