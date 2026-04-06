"""
Persistent Logging System for CaseStrainer
Logs survive container restarts and provide crash/restart diagnostics
"""

import logging
import os
import sys
import signal
import atexit
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
import json


class PersistentLogger:
    """
    Manages persistent logging that survives container restarts.
    Logs are written to mounted volumes and include crash diagnostics.
    """

    def __init__(self, app_name="casestrainer", log_dir="/app/logs"):
        self.app_name = app_name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Main application log (rotating)
        self.main_log = self.log_dir / f"{app_name}.log"

        # Persistent event log (startup/shutdown/crashes) - never rotates
        self.event_log = self.log_dir / f"{app_name}_events.log"

        # Crash diagnostics log
        self.crash_log = self.log_dir / f"{app_name}_crashes.log"

        # Session tracking
        self.session_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.session_file = self.log_dir / f"session_{self.session_id}.json"

        self.logger = None
        self.event_logger = None
        self.crash_logger = None

        self._setup_loggers()
        self._register_shutdown_handlers()
        self._log_startup()

    def _setup_loggers(self):
        """Setup multiple loggers with different purposes"""

        # 1. Main application logger with rotation
        self.logger = logging.getLogger(f"{self.app_name}.main")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        # Rotating file handler - keeps last 10 files of 5MB each
        main_handler = RotatingFileHandler(
            self.main_log, maxBytes=5 * 1024 * 1024, backupCount=10, encoding="utf-8"  # 5MB
        )
        main_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        main_handler.setFormatter(main_formatter)
        self.logger.addHandler(main_handler)

        # Also log to console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(main_formatter)
        self.logger.addHandler(console_handler)

        # 2. Event logger (NO rotation - keeps all startup/shutdown events)
        self.event_logger = logging.getLogger(f"{self.app_name}.events")
        self.event_logger.setLevel(logging.INFO)
        self.event_logger.propagate = False

        event_handler = logging.FileHandler(self.event_log, mode="a", encoding="utf-8")  # Append mode
        event_formatter = logging.Formatter("%(asctime)s - [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        event_handler.setFormatter(event_formatter)
        self.event_logger.addHandler(event_handler)

        # 3. Crash logger (NO rotation - keeps all crash diagnostics)
        self.crash_logger = logging.getLogger(f"{self.app_name}.crashes")
        self.crash_logger.setLevel(logging.ERROR)
        self.crash_logger.propagate = False

        crash_handler = logging.FileHandler(self.crash_log, mode="a", encoding="utf-8")
        crash_formatter = logging.Formatter("%(asctime)s - [CRASH] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        crash_handler.setFormatter(crash_formatter)
        self.crash_logger.addHandler(crash_handler)

    def _register_shutdown_handlers(self):
        """Register handlers to capture shutdown/crash events"""

        # Handle normal shutdown signals
        signal.signal(signal.SIGTERM, self._handle_shutdown_signal)
        signal.signal(signal.SIGINT, self._handle_shutdown_signal)

        # Handle Python exit
        atexit.register(self._log_shutdown)

        # Handle uncaught exceptions
        sys.excepthook = self._handle_uncaught_exception

    def _log_startup(self):
        """Log application startup with system information"""
        import platform
        import psutil

        startup_info = {
            "session_id": self.session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "python_version": sys.version,
            "platform": platform.platform(),
            "pid": os.getpid(),
            "cwd": os.getcwd(),
            "env": {
                "FLASK_ENV": os.getenv("FLASK_ENV", "unknown"),
                "REDIS_URL": "***" if os.getenv("REDIS_URL") else "not set",
                "ENABLE_VERIFICATION": os.getenv("ENABLE_VERIFICATION", "unknown"),
            },
        }

        # Get memory info
        try:
            mem = psutil.virtual_memory()
            startup_info["memory"] = {
                "total_gb": round(mem.total / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
                "percent_used": mem.percent,
            }
        except Exception:
            startup_info["memory"] = "unavailable"

        # Save session file
        with open(self.session_file, "w") as f:
            json.dump(startup_info, f, indent=2)

        # Log to event log
        self.event_logger.info("=" * 80)
        self.event_logger.info(f"[START] APPLICATION STARTUP - Session: {self.session_id}")
        self.event_logger.info("=" * 80)
        self.event_logger.info(f"PID: {startup_info['pid']}")
        self.event_logger.info(f"Python: {platform.python_version()}")
        self.event_logger.info(f"Platform: {startup_info['platform']}")
        self.event_logger.info(f"Environment: {startup_info['env']['FLASK_ENV']}")
        if startup_info.get("memory") != "unavailable":
            self.event_logger.info(
                f"Memory: {startup_info['memory']['available_gb']}GB available "
                f"/ {startup_info['memory']['total_gb']}GB total "
                f"({startup_info['memory']['percent_used']}% used)"
            )
        self.event_logger.info("=" * 80)

        self.logger.info(f"Persistent logging initialized - Session: {self.session_id}")
        self.logger.info(f"Main log: {self.main_log}")
        self.logger.info(f"Event log: {self.event_log}")
        self.logger.info(f"Crash log: {self.crash_log}")

    def _log_shutdown(self):
        """Log normal application shutdown"""
        try:
            # Calculate uptime
            session_data = {}
            if self.session_file.exists():
                with open(self.session_file, "r") as f:
                    session_data = json.load(f)

            start_time = datetime.fromisoformat(session_data.get("timestamp", datetime.utcnow().isoformat()))
            uptime = datetime.utcnow() - start_time

            import sys
            if not getattr(sys.stdout, 'closed', False):
                self.event_logger.info("=" * 80)
                self.event_logger.info(f"[STOP] NORMAL SHUTDOWN - Session: {self.session_id}")
                self.event_logger.info(f"Uptime: {uptime}")
                self.event_logger.info("=" * 80)

            # Update session file
            if self.session_file.exists():
                session_data["shutdown_time"] = datetime.utcnow().isoformat()
                session_data["uptime_seconds"] = uptime.total_seconds()
                session_data["shutdown_type"] = "normal"
                with open(self.session_file, "w") as f:
                    json.dump(session_data, f, indent=2)
        except Exception:
            pass  # Don't fail on shutdown logging

    def _handle_shutdown_signal(self, signum, frame):
        """Handle OS shutdown signals"""
        signal_name = signal.Signals(signum).name

        self.event_logger.warning("=" * 80)
        self.event_logger.warning(f"[WARNING]  SIGNAL RECEIVED: {signal_name} ({signum})")
        self.event_logger.warning(f"Session: {self.session_id}")
        self.event_logger.warning("=" * 80)

        # Update session file
        if self.session_file.exists():
            try:
                with open(self.session_file, "r") as f:
                    session_data = json.load(f)
                session_data["shutdown_time"] = datetime.utcnow().isoformat()
                session_data["shutdown_type"] = f"signal_{signal_name}"
                session_data["signal_number"] = signum
                with open(self.session_file, "w") as f:
                    json.dump(session_data, f, indent=2)
            except Exception:
                pass

        # Call original handler or exit
        sys.exit(0)

    def _handle_uncaught_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions - log before crash"""

        # Format exception
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tb_text = "".join(tb_lines)

        # Log to crash log
        self.crash_logger.error("=" * 80)
        self.crash_logger.error(f"[CRASH] UNCAUGHT EXCEPTION - Session: {self.session_id}")
        self.crash_logger.error("=" * 80)
        self.crash_logger.error(f"Exception Type: {exc_type.__name__}")
        self.crash_logger.error(f"Exception Value: {exc_value}")
        self.crash_logger.error("Traceback:")
        self.crash_logger.error(tb_text)
        self.crash_logger.error("=" * 80)

        # Log to event log
        self.event_logger.error("=" * 80)
        self.event_logger.error(f"[CRASH] APPLICATION CRASH - Session: {self.session_id}")
        self.event_logger.error(f"Exception: {exc_type.__name__}: {exc_value}")
        self.event_logger.error("=" * 80)

        # Update session file
        if self.session_file.exists():
            try:
                with open(self.session_file, "r") as f:
                    session_data = json.load(f)
                session_data["crash_time"] = datetime.utcnow().isoformat()
                session_data["crash_type"] = "uncaught_exception"
                session_data["exception_type"] = exc_type.__name__
                session_data["exception_message"] = str(exc_value)
                with open(self.session_file, "w") as f:
                    json.dump(session_data, f, indent=2)
            except Exception:
                pass

        # Call default exception handler
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    def log_critical_event(self, message, **kwargs):
        """Log a critical event that might indicate problems"""
        self.event_logger.warning(f"[WARNING]  {message}")
        if kwargs:
            self.event_logger.warning(f"   Details: {kwargs}")
        self.logger.warning(message, extra=kwargs)

    def log_health_check(self, status, details=None):
        """Log health check results"""
        level = logging.INFO if status == "healthy" else logging.WARNING
        msg = f"Health Check: {status}"
        if details:
            msg += f" - {details}"
        self.logger.log(level, msg)

    def log_memory_warning(self, memory_mb, threshold_mb):
        """Log memory usage warnings"""
        msg = f"Memory usage high: {memory_mb}MB / {threshold_mb}MB threshold"
        self.event_logger.warning(f"[WARNING]  {msg}")
        self.logger.warning(msg)

    def get_logger(self):
        """Get the main application logger"""
        return self.logger

    def attach_main_handler_to_root(self):
        """Attach the main logger's file and console handlers to the root logger so that all
        propagating loggers (e.g. src.verification.batch, src.verification.master) write to the
        same worker log file and to stdout (docker logs). Call this only in worker processes."""
        root = logging.getLogger()
        for h in self.logger.handlers:
            if isinstance(h, (logging.FileHandler, RotatingFileHandler, logging.StreamHandler)):
                root.addHandler(h)
                root.setLevel(min(root.level, logging.INFO))
        # Do not return after first handler: attach both file and console so BATCH logs appear in docker logs

    def get_event_logger(self):
        """Get the event logger"""
        return self.event_logger

    def get_crash_logger(self):
        """Get the crash logger"""
        return self.crash_logger


# Global instance
_persistent_logger = None


def init_persistent_logging(app_name="casestrainer", log_dir="/app/logs"):
    """Initialize persistent logging system"""
    global _persistent_logger
    if _persistent_logger is None:
        _persistent_logger = PersistentLogger(app_name, log_dir)
    return _persistent_logger


def get_persistent_logger():
    """Get the global persistent logger instance"""
    global _persistent_logger
    if _persistent_logger is None:
        _persistent_logger = init_persistent_logging()
    return _persistent_logger
