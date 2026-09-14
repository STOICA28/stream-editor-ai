import logging

import structlog


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(level=level, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict[str, Any],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

from typing import Any


def get_logger(name: str) -> Any:
    return structlog.get_logger(name)

def log_pipeline_step(logger: Any, project_id: str, job_id: str, stage: str, **kwargs: Any) -> None:
    logger.info("pipeline_step", project_id=project_id, job_id=job_id, stage=stage, **kwargs)
