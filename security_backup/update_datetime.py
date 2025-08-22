with open("app_final_vue.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace all instances of datetime.utcnow() with timezone-aware version
updated_content = content.replace("datetime.utcnow()", "datetime.now(timezone.utc)")

# Write the updated content back to the file
with open("app_final_vue.py", "w", encoding="utf-8") as f:
    f.write(updated_content)
