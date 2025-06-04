import os
import glob
from datetime import datetime, timedelta


def get_latest_log_file():
    # Look for log files in the standard locations
    log_dirs = [
        "logs",
        "log",
        os.path.join("src", "logs"),
        os.path.join("src", "log"),
    ]

    # Also check the current directory
    log_dirs.append(".")

    log_files = []
    for log_dir in log_dirs:
        if os.path.exists(log_dir):
            log_files.extend(glob.glob(os.path.join(log_dir, "*.log")))

    # Sort by modification time, newest first
    if log_files:
        return max(log_files, key=os.path.getmtime)
    return None


def print_recent_logs(log_file, lines=50):
    try:
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            # Get all lines and filter recent ones (last hour)
            all_lines = f.readlines()
            recent_lines = [line for line in all_lines if is_recent_line(line)]

            # If not enough recent lines, take the last 'lines' lines
            if len(recent_lines) < 10 and all_lines:
                recent_lines = all_lines[-lines:]

            print(f"\n=== Last {len(recent_lines)} lines from {log_file} ===\n")
            print("".join(recent_lines))

    except Exception as e:
        print(f"Error reading log file: {e}")


def is_recent_line(line):
    # Try to extract timestamp from the line
    try:
        # Common log formats: [2023-01-01 12:34:56] or 2023-01-01 12:34:56
        if "]" in line and "[" in line:
            timestamp_str = line.split("[")[1].split("]")[0].strip()
        else:
            # Try to find a timestamp at the start of the line
            timestamp_str = " ".join(line.split()[:2])

        # Try different datetime formats
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S,%f"]:
            try:
                log_time = datetime.strptime(timestamp_str, fmt)
                # Check if log entry is from the last hour
                return (datetime.now() - log_time) < timedelta(hours=1)
            except ValueError:
                continue
    except:
        pass

    return False


def main():
    print("Checking for server logs...")
    log_file = get_latest_log_file()

    if log_file:
        print(f"Found log file: {log_file}")
        print_recent_logs(log_file)
    else:
        print("No log files found in common locations.")
        print("Please check the server output for any error messages.")


if __name__ == "__main__":
    main()
