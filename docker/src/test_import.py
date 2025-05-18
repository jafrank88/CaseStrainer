import sys
import traceback

try:
    print("Attempting to import app_final...")
    import app_final
    print("Successfully imported app_final")
except Exception as e:
    print(f"Error importing app_final: {e}")
    traceback.print_exc()

try:
    print("\nAttempting to import serve_vue...")
    import serve_vue
    print("Successfully imported serve_vue")
except Exception as e:
    print(f"Error importing serve_vue: {e}")
    traceback.print_exc()

try:
    print("\nAttempting to import app_final_vue...")
    import app_final_vue
    print("Successfully imported app_final_vue")
except Exception as e:
    print(f"Error importing app_final_vue: {e}")
    traceback.print_exc()
