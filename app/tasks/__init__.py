try:
    from .data_quality_tasks import (
        celery_app, analyze_data_quality_task, clean_data_task, generate_report_task
    )
    DATA_QUALITY_AVAILABLE = True
    __all__ = [
        "celery_app", "analyze_data_quality_task", "clean_data_task", "generate_report_task"
    ]
except ImportError as e:
    print(f"Data quality tasks not available: {e}")
    DATA_QUALITY_AVAILABLE = False
    __all__ = []