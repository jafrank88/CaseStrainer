#!/usr/bin/env python3
"""
Test progress manager directly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import asyncio
from src.progress_manager import SSEProgressManager, ChunkedCitationProcessor

async def test_progress_manager():
    """Test progress manager directly"""
    
    print("🧪 Testing SSE Progress Manager directly...")
    
    # Create test text
    test_text = "This is a test. Smith v. Jones, 123 F.3d 456. Another case: Johnson v. Smith, 789 F.2d 234."
    
    try:
        # Initialize progress manager
        progress_manager = SSEProgressManager()
        processor = ChunkedCitationProcessor(progress_manager)
        
        print(f"📝 Test text length: {len(test_text)} characters")
        
        # Submit async task
        task_id = await processor.process_document_with_progress(test_text, "legal_brief")
        
        print(f"✅ Task submitted with ID: {task_id}")
        
        # Check progress
        for i in range(10):
            await asyncio.sleep(1)
            
            if task_id in progress_manager.active_tasks:
                tracker = progress_manager.active_tasks[task_id]
                progress_data = tracker.get_progress_data()
                print(f"📊 Progress: {progress_data['progress']}% - {progress_data['message']}")
                
                if tracker.is_complete():
                    print(f"✅ Task completed!")
                    print(f"📊 Results: {len(tracker.results)} citations found")
                    return True
            else:
                print(f"⚠️  Task {task_id} not found in active tasks")
        
        print("⏰ Test timeout reached")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_progress_manager())
    
    if success:
        print("\n✅ Progress Manager test completed successfully!")
    else:
        print("\n❌ Progress Manager test failed!")
