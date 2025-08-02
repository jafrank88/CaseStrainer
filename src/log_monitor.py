import os
import time
import re
import logging
from datetime import datetime
from colorama import init, Fore, Style

# Set up logging
logger = logging.getLogger(__name__)

# Initialize colorama for colored terminal output
init()

# Configuration
LOG_FILE = "logs/casestrainer.log"
POLL_INTERVAL = 1.0  # seconds
MAX_LINES = 100  # Maximum number of lines to display when starting


def create_log_dir():
    """Create logs directory if it doesn't exist"""
    log_dir = os.path.dirname(LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        with open(LOG_FILE, "w") as f:
            f.write(f"{datetime.now()} - Log monitor initialized\n")


def get_file_size(file_path):
    """Get the size of a file in bytes"""
    try:
        return os.path.getsize(file_path)
    except FileNotFoundError:
        return 0


def colorize_log_line(line):
    """Add color to log lines based on content"""
    if re.search(r"ERROR|CRITICAL|Exception|Traceback", line, re.IGNORECASE):
        return f"{Fore.RED}{line}{Style.RESET_ALL}"
    elif re.search(r"WARNING", line, re.IGNORECASE):
        return f"{Fore.YELLOW}{line}{Style.RESET_ALL}"
    elif re.search(r"INFO", line, re.IGNORECASE):
        return f"{Fore.GREEN}{line}{Style.RESET_ALL}"
    elif re.search(r"DEBUG", line, re.IGNORECASE):
        return f"{Fore.CYAN}{line}{Style.RESET_ALL}"
    elif re.search(
        r"enhanced.validator|citation.context|validation", line, re.IGNORECASE
    ):
        return f"{Fore.MAGENTA}{line}{Style.RESET_ALL}"
    else:
        return line


def tail_log_file(file_path, follow=True):
    """
    Display the last lines of a log file and optionally follow it
    Similar to 'tail -f' in Unix
    """
    try:
        # Create log directory and file if they don't exist
        create_log_dir()

        # Get initial file size
        file_size = get_file_size(file_path)

        # If file exists and has content, show the last MAX_LINES lines
        if file_size > 0:
            with open(file_path, "r") as f:
                lines = f.readlines()
                start_idx = max(0, len(lines) - MAX_LINES)
                for line in lines[start_idx:]:
                    logger.info(colorize_log_line(line.rstrip()))

        # If not following, exit after showing the initial lines
        if not follow:
            return

        # Print separator to indicate we're now following
        logger.info(f"\n{Fore.CYAN}=== Following log file: {file_path} (Ctrl+C to exit) ==={Style.RESET_ALL}\n"
        )

        # Follow the file for new content
        last_size = file_size
        try:
            while True:
                current_size = get_file_size(file_path)

                # If file has grown
                if current_size > last_size:
                    with open(file_path, "r") as f:
                        f.seek(last_size)
                        for line in f:
                            logger.info(colorize_log_line(line.rstrip()))

                    last_size = current_size

                # If file has been truncated or deleted
                elif current_size < last_size:
                    logger.info(f"{Fore.YELLOW}Log file was truncated or deleted. Restarting...{Style.RESET_ALL}")
                    last_size = 0

                time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            logger.info(f"\n{Fore.CYAN}Log monitoring stopped.{Style.RESET_ALL}")

    except Exception as e:
        logger.error(f"{Fore.RED}Error monitoring log file: {str(e)}{Style.RESET_ALL}")


if __name__ == "__main__":
    logger.info(f"{Fore.CYAN}CaseStrainer Log Monitor{Style.RESET_ALL}")
    logger.info(f"Monitoring log file: {LOG_FILE}")

    # Check if log file exists
    if not os.path.exists(LOG_FILE):
        logger.info(f"{Fore.YELLOW}Log file does not exist. Creating it...{Style.RESET_ALL}")
        create_log_dir()

    # Start monitoring
    tail_log_file(LOG_FILE)
