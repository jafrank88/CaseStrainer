import os
import sys
import traceback
import logging
import importlib
from datetime import datetime

try:
    from dotenv import load_dotenv

    load_dotenv()  # Load environment variables from .env file
except ImportError:
    print(
        "Warning: python-dotenv not installed. Some environment variables might be missing."
    )

try:
    import pkg_resources

    PKG_RESOURCES_AVAILABLE = True
except ImportError:
    PKG_RESOURCES_AVAILABLE = False

# Configure logging to both file and console
# Use project root logs directory
project_root = os.path.dirname(os.path.abspath(__file__))
logs_dir = os.path.join(project_root, "logs")
os.makedirs(logs_dir, exist_ok=True)

log_file = os.path.join(logs_dir, "flask_debug.log")
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode="w"),  # Overwrite log file
        logging.StreamHandler(sys.stdout),  # Also log to console
    ],
)
logger = logging.getLogger(__name__)


def log(message, level="info"):
    """Helper function to log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"{timestamp} - {message}"

    # Write to log file
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_message + "\n")

    # Also print to console
    print(log_message)

    # Log using appropriate level
    getattr(logger, level.lower(), logger.info)(message)


def check_imports():
    """Check if all required packages are importable"""
    required_packages = [
        "flask",
        "flask_cors",
        "flask_mail",
        "flask_session",
        "werkzeug",
        "requests",
        "sqlalchemy",
        "PyPDF2",
        "docx2txt",
        "beautifulsoup4",
        "python-dotenv",
        "python-magic",
        "pytz",
        "python-dateutil",
    ]

    log("\nChecking required packages...")
    if not PKG_RESOURCES_AVAILABLE:
        log("⚠ pkg_resources not available, using basic import checking", "warning")

    missing_packages = []
    for pkg in required_packages:
        try:
            importlib.import_module(pkg.replace("-", "_"))
            log(f"✓ {pkg} is importable")
        except ImportError as e:
            missing_packages.append(pkg)
            log(f"✗ {pkg} is NOT importable: {str(e)}", "error")

    if missing_packages:
        log(
            f"\nMissing or unimportable packages: {', '.join(missing_packages)}",
            "error",
        )
        log(
            "You can install missing packages with: pip install "
            + " ".join(missing_packages),
            "info",
        )
        return False
    return True


def check_environment():
    """Check if required environment variables are set"""
    required_vars = [
        "FLASK_APP",
        "FLASK_ENV",
        "SECRET_KEY",
        "DATABASE_URL",
        "MAIL_SERVER",
        "MAIL_USERNAME",
        "MAIL_PASSWORD",
    ]

    log("\nChecking environment variables...")
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value is not None and value.strip() != "":
            # For sensitive variables, just log that they're set but not their values
            if "PASSWORD" in var or "SECRET" in var or "KEY" in var:
                log(f"✓ {var} is set")
            else:
                log(f"✓ {var} = {value}")
        else:
            missing_vars.append(var)
            log(f"✗ Missing or empty environment variable: {var}", "error")

    if missing_vars:
        log(f"\nMissing environment variables: {', '.join(missing_vars)}", "warning")
        log("Please set these variables in your .env file or environment", "info")
        return False
    return True


def check_directories():
    """Check required directories exist and are writable"""
    log("\nChecking directories...")
    required_dirs = ["uploads", "logs", "instance"]

    for dir_name in required_dirs:
        try:
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
                log(f"✓ Created directory: {dir_name}")

            # Test write permission
            test_file = os.path.join(dir_name, "test.txt")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            log(f"✓ Directory is writable: {dir_name}")

        except Exception as e:
            log(f"✗ Error with directory {dir_name}: {str(e)}", "error")
            return False
    return True


def main():
    try:
        log("=" * 80)
        log(f"Starting CaseStrainer Debug - {datetime.now()}")
        log("=" * 80)

        # Basic system info
        log("\nSystem Information:")
        log(f"Python: {sys.version}")
        log(f"Working Directory: {os.getcwd()}")
        log(f"Python Path: {sys.path}")

        # Check environment
        if not all([check_imports(), check_environment(), check_directories()]):
            log("\nPre-flight checks failed. Please fix the issues above.", "error")
            input("\nPress Enter to exit...")
            return 1

        # Try to import and create the app
        log("\nAttempting to import app_final_vue...")
        try:
            from src.app_final_vue import create_app

            log("✓ Successfully imported create_app from src.app_final_vue")

            log("\nCreating Flask application...")
            try:
                app = create_app()
                log("✓ Flask application created successfully")
                log(f"Application Name: {app.name}")
                log(f"Instance Path: {app.instance_path}")
                log(f"Debug Mode: {app.debug}")

                # Log some important config values
                log("\nApplication Configuration:")
                for key in [
                    "DEBUG",
                    "SECRET_KEY",
                    "SQLALCHEMY_DATABASE_URI",
                    "MAIL_SERVER",
                ]:
                    log(
                        f"{key}: {'*' * 8 if 'KEY' in key or 'SECRET' in key else app.config.get(key, 'Not Set')}"
                    )

                # Start the server
                log("\n" + "=" * 40)
                log("Starting Flask development server...")
                log("Local:   http://127.0.0.1:5000/")
                log(f"Network: http://{os.environ.get('HOSTNAME', 'localhost')}:5000/")
                log("=" * 40 + "\n")

                app.run(
                    host="0.0.0.0",
                    port=5000,
                    debug=True,
                    use_reloader=False,  # Disable reloader to avoid double output
                    threaded=True,
                )

            except Exception as e:
                log(f"\nError creating Flask application: {str(e)}", "error")
                log("\nTraceback:", "error")
                log(traceback.format_exc(), "error")
                raise

        except ImportError as e:
            log(f"\nFailed to import app_final_vue: {str(e)}", "error")
            log("\nCurrent directory contents:", "debug")
            log("\n".join([f"  - {f}" for f in os.listdir(".")]), "debug")

            if os.path.exists("src"):
                log("\nsrc directory contents:", "debug")
                log("\n".join([f"  - {f}" for f in os.listdir("src")]), "debug")

            if os.path.exists("casestrainer-vue"):
                log("\ncasestrainer-vue directory contents:", "debug")
                log(
                    "\n".join([f"  - {f}" for f in os.listdir("casestrainer-vue")]),
                    "debug",
                )

            raise

    except Exception as e:
        log("\n" + "!" * 60, "error")
        log(f"FATAL ERROR: {type(e).__name__}", "error")
        log(f"Message: {str(e)}", "error")
        log("\nTraceback:", "error")
        log(traceback.format_exc(), "error")
        log("!" * 60, "error")

        # Additional debug info
        log("\nAdditional debug info:", "debug")
        log(f"Current directory: {os.getcwd()}", "debug")
        log(f"Environment variables: {os.environ}", "debug")

        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
