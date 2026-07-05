"""
Memory Integration Scheduler Service

Handles time-based triggers for memory integration tasks using APScheduler.
"""
import asyncio
import logging
from typing import Optional, Callable
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.memory import MemoryJobStore

from services.memory_service import MemoryService, SummaryType

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Scheduler service for memory integration tasks.
    
    Manages:
    - Daily summary generation
    - Weekly summary generation
    - Monthly summary generation
    - Manual task triggers
    """
    
    _instance: Optional["SchedulerService"] = None
    
    def __init__(self):
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._memory_service = MemoryService()
        self._initialized = False
    
    @classmethod
    def get_instance(cls) -> "SchedulerService":
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = SchedulerService()
        return cls._instance
    
    def initialize(self):
        """Initialize the scheduler"""
        if self._initialized:
            return
        
        self._scheduler = AsyncIOScheduler(
            jobstores={"default": MemoryJobStore()},
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 3600,  # 1 hour grace period
            },
        )
        self._initialized = True
        logger.info("Scheduler service initialized")
    
    def start(self):
        """Start the scheduler"""
        if not self._initialized:
            self.initialize()
        
        if self._scheduler and not self._scheduler.running:
            self._scheduler.start()
            logger.info("Scheduler started")
            
            # Schedule tasks based on current configuration
            asyncio.create_task(self._sync_schedule_from_config())
    
    def stop(self):
        """Stop the scheduler"""
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")
    
    async def _sync_schedule_from_config(self):
        """Sync scheduler with configuration from memory status"""
        status = await self._memory_service.get_status()
        
        # Daily summary
        if status.daily_schedule_enabled:
            hour, minute = map(int, status.daily_schedule_time.split(":"))
            self._add_daily_job(
                "daily_summary",
                self._run_daily_summary,
                hour=hour,
                minute=minute,
            )
        else:
            self._remove_job("daily_summary")
        
        # Weekly summary
        if status.weekly_schedule_enabled:
            hour, minute = map(int, status.weekly_schedule_time.split(":"))
            self._add_weekly_job(
                "weekly_summary",
                self._run_weekly_summary,
                day_of_week=status.weekly_schedule_day,
                hour=hour,
                minute=minute,
            )
        else:
            self._remove_job("weekly_summary")
        
        # Monthly summary
        if status.monthly_schedule_enabled:
            hour, minute = map(int, status.monthly_schedule_time.split(":"))
            self._add_monthly_job(
                "monthly_summary",
                self._run_monthly_summary,
                day=status.monthly_schedule_day,
                hour=hour,
                minute=minute,
            )
        else:
            self._remove_job("monthly_summary")
    
    async def _run_daily_summary(self):
        """Execute daily summary generation"""
        logger.info("Running scheduled daily summary...")
        try:
            result = await self._memory_service.generate_summary(SummaryType.DAILY)
            if result.error:
                logger.error(f"Daily summary failed: {result.error}")
            else:
                logger.info(f"Daily summary created: {result.summary_id}")
        except Exception as e:
            logger.error(f"Daily summary error: {e}")
    
    async def _run_weekly_summary(self):
        """Execute weekly summary generation"""
        logger.info("Running scheduled weekly summary...")
        try:
            result = await self._memory_service.generate_summary(SummaryType.WEEKLY)
            if result.error:
                logger.error(f"Weekly summary failed: {result.error}")
            else:
                logger.info(f"Weekly summary created: {result.summary_id}")
        except Exception as e:
            logger.error(f"Weekly summary error: {e}")
    
    async def _run_monthly_summary(self):
        """Execute monthly summary generation"""
        logger.info("Running scheduled monthly summary...")
        try:
            result = await self._memory_service.generate_summary(SummaryType.MONTHLY)
            if result.error:
                logger.error(f"Monthly summary failed: {result.error}")
            else:
                logger.info(f"Monthly summary created: {result.summary_id}")
        except Exception as e:
            logger.error(f"Monthly summary error: {e}")
    
    async def run_integration(self):
        """Execute full memory integration"""
        logger.info("Running scheduled memory integration...")
        try:
            result = await self._memory_service.run_integration(include_summary=False)
            logger.info(f"Memory integration completed: {result}")
            return result
        except Exception as e:
            logger.error(f"Memory integration error: {e}")
            raise
    
    def _add_daily_job(
        self,
        job_id: str,
        func: Callable,
        hour: int = 9,
        minute: int = 0,
    ):
        """Add or update a daily recurring job"""
        if not self._scheduler:
            return
        
        self._scheduler.add_job(
            func,
            CronTrigger(hour=hour, minute=minute),
            id=job_id,
            replace_existing=True,
        )
        logger.info(f"Daily job '{job_id}' scheduled for {hour:02d}:{minute:02d}")
    
    def _add_weekly_job(
        self,
        job_id: str,
        func: Callable,
        day_of_week: int = 0,  # 0=Monday, 6=Sunday
        hour: int = 9,
        minute: int = 0,
    ):
        """Add or update a weekly recurring job"""
        if not self._scheduler:
            return
        
        self._scheduler.add_job(
            func,
            CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute),
            id=job_id,
            replace_existing=True,
        )
        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        logger.info(f"Weekly job '{job_id}' scheduled for {day_names[day_of_week]} {hour:02d}:{minute:02d}")
    
    def _add_monthly_job(
        self,
        job_id: str,
        func: Callable,
        day: int = 1,
        hour: int = 9,
        minute: int = 0,
    ):
        """Add or update a monthly recurring job"""
        if not self._scheduler:
            return
        
        self._scheduler.add_job(
            func,
            CronTrigger(day=day, hour=hour, minute=minute),
            id=job_id,
            replace_existing=True,
        )
        logger.info(f"Monthly job '{job_id}' scheduled for day {day} at {hour:02d}:{minute:02d}")
    
    def _remove_job(self, job_id: str):
        """Remove a job from the scheduler"""
        if not self._scheduler:
            return
        
        try:
            self._scheduler.remove_job(job_id)
            logger.info(f"Job '{job_id}' removed")
        except Exception:
            pass  # Job might not exist
    
    def get_scheduled_jobs(self) -> list:
        """Get list of scheduled jobs"""
        if not self._scheduler or not self._scheduler.running:
            return []
        
        jobs = []
        for job in self._scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
            })
        return jobs
    
    async def update_schedule_and_restart(
        self,
        daily_enabled: Optional[bool] = None,
        weekly_enabled: Optional[bool] = None,
        monthly_enabled: Optional[bool] = None,
        daily_time: Optional[str] = None,
        weekly_day: Optional[int] = None,
        weekly_time: Optional[str] = None,
        monthly_day: Optional[int] = None,
        monthly_time: Optional[str] = None,
    ):
        """Update schedule configuration and restart scheduler"""
        # Update config
        await self._memory_service.update_schedule(
            daily_enabled=daily_enabled,
            weekly_enabled=weekly_enabled,
            monthly_enabled=monthly_enabled,
            daily_time=daily_time,
            weekly_day=weekly_day,
            weekly_time=weekly_time,
            monthly_day=monthly_day,
            monthly_time=monthly_time,
        )
        
        # Sync scheduler
        await self._sync_schedule_from_config()
        
        return await self._memory_service.get_status()
    
    def run_job_now(self, job_id: str):
        """Trigger a job to run immediately"""
        if not self._scheduler:
            return {"error": "Scheduler not initialized"}
        
        job = self._scheduler.get_job(job_id)
        if not job:
            return {"error": f"Job '{job_id}' not found"}
        
        # Run the job's func immediately
        asyncio.create_task(job.func())
        return {"message": f"Job '{job_id}' triggered", "job_id": job_id}


# Global scheduler instance
scheduler_service = SchedulerService.get_instance()
