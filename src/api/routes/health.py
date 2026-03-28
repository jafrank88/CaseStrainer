"""
Health and database stats routes for the Vue API.
"""

import os
import sys
import logging
import traceback
from datetime import datetime

from flask import request, jsonify, current_app

from src.database_manager import get_database_manager
from src.config import IS_PRODUCTION, REDIS_URL

logger = logging.getLogger(__name__)


def register_health_routes(bp):
    @bp.route("/health", methods=["GET"])
    def health_check():
        """Enhanced health check endpoint with detailed diagnostics"""
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "unknown",
            "components": {},
            "database_stats": {},
            "environment": {"python_version": sys.version.split()[0], "platform": sys.platform},
            "endpoints": {"current": "/casestrainer/api/health", "alias": "/health", "base_url": request.base_url},
        }

        try:
            try:
                version_path = os.path.join("/app", "VERSION")
                if os.path.exists(version_path):
                    with open(version_path, "r", encoding="utf-8") as vf:
                        health_data["version"] = vf.read().strip()
                else:
                    health_data["version"] = "development"
                    logger.warning("VERSION file not found, using 'development'")
            except Exception as e:
                health_data["version"] = "error"
                health_data["components"]["version_check"] = f"error: {str(e)}"
                logger.warning(f"Could not read VERSION file: {e}")

            try:
                db_manager = get_database_manager()
                db_stats = db_manager.get_database_stats()
                health_data["components"]["database"] = "healthy"
                health_data["database_stats"] = {
                    "tables": len(db_stats.get("tables", {})),
                    "size_mb": round(db_stats.get("database_size_mb", 0), 2),
                    "path": os.path.abspath(db_manager.db_path) if hasattr(db_manager, "db_path") else "unknown",
                }
            except Exception as e:
                health_data["status"] = "degraded"
                health_data["components"]["database"] = f"error: {str(e)}"
                logger.error(f"Database check failed: {e}")

            try:
                upload_dir = os.path.join(current_app.root_path, "uploads")
                if os.path.isdir(upload_dir) and os.access(upload_dir, os.W_OK):
                    health_data["components"]["upload_directory"] = "healthy"
                else:
                    health_data["status"] = "degraded"
                    health_data["components"]["upload_directory"] = "unwritable"
            except Exception as e:
                health_data["status"] = "degraded"
                health_data["components"]["upload_directory"] = f"error: {str(e)}"

            try:
                health_data["components"]["citation_processor"] = "healthy"
            except Exception as e:
                health_data["status"] = "degraded"
                health_data["components"]["citation_processor"] = f"error: {str(e)}"
                logger.error(f"Citation processor check failed: {e}")

            try:
                import redis
                r = redis.from_url(REDIS_URL)
                r.ping()
                health_data["components"]["redis"] = "healthy"
            except Exception as e:
                health_data["status"] = "degraded"
                health_data["components"]["redis"] = f"error: {str(e)}"
                logger.warning(f"Redis check failed: {e}")

            status_code = 200 if health_data["status"] == "healthy" else 207
            return jsonify(health_data), status_code

        except Exception as e:
            logger.error(f"Health check failed completely: {e}", exc_info=True)
            payload = {"status": "unhealthy", "error": str(e)}
            if not IS_PRODUCTION:
                payload["traceback"] = str(traceback.format_exc())
            health_data.update(payload)
            return jsonify(health_data), 500

    @bp.route("/casestrainer/api/health", methods=["GET"])
    def health_check_alias():
        return health_check()

    @bp.route("/db_stats", methods=["GET"])
    def db_stats():
        """Database statistics endpoint"""
        try:
            db_manager = get_database_manager()
            stats = db_manager.get_database_stats()
            return jsonify(stats)
        except Exception as e:
            logger.error(f"Database stats error: {e}")
            return jsonify({"error": "Database stats unavailable"}), 503
