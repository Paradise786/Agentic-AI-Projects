import datetime
import logging
import sys
import subprocess
from typing import Callable, Optional

# --- Auto-install missing packages ---
def _ensure_package(import_name: str, pip_name: str = None):
    """Try importing a package; if missing, install it automatically."""
    pip_name = pip_name or import_name
    try:
        __import__(import_name)
    except ImportError:
        print(f"[auto-install] Installing missing package: {pip_name}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])

_ensure_package("apscheduler", "apscheduler")
# --- End auto-install ---

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import Reminder

logger = logging.getLogger(__name__)

class ReminderService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.send_callback: Optional[Callable[[int, str, int], None]] = None
        self.is_running = False

    def start(self):
        """Starts the scheduler if enabled and not already running."""
        if not settings.SCHEDULER_ENABLED:
            logger.info("Scheduler is disabled in configuration.")
            return

        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("APScheduler initialized and running.")
            self._load_active_reminders()

    def set_callback(self, callback: Callable[[int, str, int], None]):
        """Sets the bot notification sender function callback."""
        self.send_callback = callback

    def shutdown(self):
        """Shutdown scheduler thread."""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("APScheduler shut down successfully.")

    def _load_active_reminders(self):
        """Loads active reminders from the database on startup."""
        db: Session = SessionLocal()
        try:
            now = datetime.datetime.utcnow()
            active_reminders = db.query(Reminder).filter(
                Reminder.status == "active"
            ).all()

            count = 0
            for r in active_reminders:
                # For non-recurring reminders in the past, complete them immediately or trigger
                if not r.is_recurring and r.target_time < now:
                    r.status = "completed"
                    logger.info(f"Marking past reminder {r.id} as completed.")
                else:
                    self._schedule_job(r)
                    count += 1
            db.commit()
            logger.info(f"Scheduled {count} active reminders from database.")
        except Exception as e:
            logger.error(f"Error loading active reminders from database: {e}")
        finally:
            db.close()

    def _schedule_job(self, reminder: Reminder):
        """Helper to append a job to APScheduler."""
        job_id = f"reminder_{reminder.id}"
        
        # Avoid duplicate scheduling
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        if reminder.is_recurring and reminder.cron_expr:
            try:
                # Handle standard cron strings
                self.scheduler.add_job(
                    func=self._trigger_reminder,
                    trigger=CronTrigger.from_crontab(reminder.cron_expr),
                    args=[reminder.user_id, reminder.text, reminder.id],
                    id=job_id
                )
            except Exception as e:
                logger.error(f"Failed to parse cron trigger '{reminder.cron_expr}' for reminder {reminder.id}: {e}")
        else:
            self.scheduler.add_job(
                func=self._trigger_reminder,
                trigger="date",
                run_date=reminder.target_time,
                args=[reminder.user_id, reminder.text, reminder.id],
                id=job_id
            )

    def add_reminder(self, db: Session, user_id: int, text: str, target_time: datetime.datetime, is_recurring: bool = False, cron_expr: Optional[str] = None) -> Reminder:
        """Saves a reminder to database and schedules it."""
        reminder = Reminder(
            user_id=user_id,
            text=text,
            target_time=target_time,
            is_recurring=is_recurring,
            cron_expr=cron_expr,
            status="active"
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)

        if self.is_running:
            self._schedule_job(reminder)

        return reminder

    def cancel_reminder(self, db: Session, reminder_id: int) -> bool:
        """Cancels a reminder job and marks it as cancelled in DB."""
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if not reminder:
            return False

        reminder.status = "cancelled"
        db.commit()

        job_id = f"reminder_{reminder_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info(f"Cancelled scheduled job {job_id}")

        return True

    def _trigger_reminder(self, user_id: int, text: str, reminder_id: int):
        """Called when a scheduled reminder is triggered."""
        logger.info(f"Triggering reminder {reminder_id} for user {user_id}")
        
        # Fire bot notification callback
        if self.send_callback:
            try:
                self.send_callback(user_id, text, reminder_id)
            except Exception as e:
                logger.error(f"Error calling send_callback in reminder trigger: {e}")
        else:
            logger.warning(f"Reminder callback not set! Notification context: {text}")

        # Update non-recurring reminder status to completed
        db: Session = SessionLocal()
        try:
            reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
            if reminder and not reminder.is_recurring:
                reminder.status = "completed"
                db.commit()
        except Exception as e:
            logger.error(f"Failed to update reminder status in database: {e}")
        finally:
            db.close()

reminder_service = ReminderService()
