"""
Script to check and manage running Python/Flask processes
"""
import os
import sys
import ctypes
import psutil
import signal

def check_processes():
    """Check for running Python/Flask processes"""
    print("=== CHECKING RUNNING PYTHON/FLASK PROCESSES ===\n")
    
    # Find all Python processes
    python_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'flask' in cmdline.lower() or 'app_final_vue' in cmdline:
                    python_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    # Print process information
    if not python_processes:
        print("No Python/Flask processes found.")
        return []
    
    print(f"Found {len(python_processes)} Python/Flask process(es):\n")
    for i, proc in enumerate(python_processes, 1):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            print(f"Process {i}:")
            print(f"  PID: {proc.info['pid']}")
            print(f"  Name: {proc.info['name']}")
            print(f"  Command: {cmdline}")
            print()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            print(f"  Could not access process {proc.info['pid']} (access denied or process ended)\n")
    
    return python_processes

def stop_processes(processes):
    """Stop the specified processes"""
    if not processes:
        print("No processes to stop.")
        return
    
    print("\nStopping processes...")
    for proc in processes:
        try:
            p = psutil.Process(proc.info['pid'])
            p.terminate()
            print(f"  Sent termination signal to process {proc.info['pid']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            print(f"  Could not terminate process {proc.info['pid']}: {e}")
    
    # Check if processes have terminated
    print("\nWaiting for processes to terminate...")
    gone, still_alive = psutil.wait_procs(
        [psutil.Process(p.info['pid']) for p in processes],
        timeout=3,
        callback=None
    )
    
    if still_alive:
        print("\nSome processes did not terminate gracefully. Force stopping...")
        for p in still_alive:
            try:
                p.kill()
                print(f"  Force killed process {p.pid}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                print(f"  Process {p.pid} already terminated")
    
    print("\nAll processes have been stopped.")

if __name__ == "__main__":
    # Check for admin privileges
    if os.name == 'nt' and not ctypes.windll.shell32.IsUserAnAdmin():
        print("This script requires administrator privileges to manage processes.")
        print("Please run this script as administrator.")
        sys.exit(1)
    
    # Check running processes
    processes = check_processes()
    
    if processes:
        response = input("\nDo you want to stop these processes? (y/n): ")
        if response.lower() == 'y':
            stop_processes(processes)
