#!/usr/bin/env python3
"""
Check active tasks in progress manager
"""

def check_active_tasks():
    """Check what tasks are currently active"""
    try:
        from src.unified_input_processor import get_progress_manager
        pm = get_progress_manager()
        
        print('Active tasks in progress manager:')
        print(f'Total active tasks: {len(pm.active_tasks)}')
        
        for task_id, tracker in pm.active_tasks.items():
            print(f'  Task ID: {task_id}')
            print(f'    Tracker type: {type(tracker).__name__}')
            
            if hasattr(tracker, 'get_progress_data'):
                try:
                    data = tracker.get_progress_data()
                    progress = data.get('progress', 0)
                    message = data.get('message', '')
                    status = data.get('status', '')
                    print(f'    Progress: {progress}% - {status} - {message}')
                except Exception as e:
                    print(f'    Error getting progress data: {e}')
            else:
                print(f'    No get_progress_data method')
            print()
            
    except Exception as e:
        print(f'Error checking active tasks: {e}')

if __name__ == "__main__":
    check_active_tasks()
