with open("app_final_vue.py", "r", encoding="utf-8") as f:
    content = f.read()

updated_content = content.replace("datetime.utcnow()", "datetime.now(timezone.utc)")

with open("app_final_vue.py", "w", encoding="utf-8") as f:
    f.write(updated_content)
