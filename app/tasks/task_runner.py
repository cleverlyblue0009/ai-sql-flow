"""
Simple task runner for when Celery is not available
"""

import asyncio
import logging
import threading
from typing import Dict, Any, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class SimpleTaskRunner:
    """Simple in-memory task runner for development/testing"""
    
    def __init__(self):
        self.tasks = {}
        self.results = {}
        
    def delay(self, task_func: Callable, *args, **kwargs):
        """Execute task in background thread"""
        task_id = f"task_{datetime.utcnow().timestamp()}"
        
        def run_task():
            try:
                logger.info(f"Starting task {task_id}")
                result = task_func(*args, **kwargs)
                self.results[task_id] = {
                    "status": "completed",
                    "result": result,
                    "completed_at": datetime.utcnow()
                }
                logger.info(f"Task {task_id} completed successfully")
            except Exception as e:
                logger.error(f"Task {task_id} failed: {str(e)}")
                self.results[task_id] = {
                    "status": "failed",
                    "error": str(e),
                    "completed_at": datetime.utcnow()
                }
        
        # Start task in background thread
        thread = threading.Thread(target=run_task)
        thread.daemon = True
        thread.start()
        
        return SimpleTaskResult(task_id, self)
    
    def get_result(self, task_id: str):
        """Get task result"""
        return self.results.get(task_id)


class SimpleTaskResult:
    """Simple task result wrapper"""
    
    def __init__(self, task_id: str, runner: SimpleTaskRunner):
        self.task_id = task_id
        self.runner = runner
        
    def get(self, timeout=None):
        """Get task result (blocking)"""
        import time
        start_time = time.time()
        
        while True:
            result = self.runner.get_result(self.task_id)
            if result:
                if result["status"] == "completed":
                    return result["result"]
                elif result["status"] == "failed":
                    raise Exception(result["error"])
            
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError("Task timeout")
            
            time.sleep(0.1)
    
    @property
    def status(self):
        """Get task status"""
        result = self.runner.get_result(self.task_id)
        return result["status"] if result else "pending"


# Global task runner instance
simple_task_runner = SimpleTaskRunner()