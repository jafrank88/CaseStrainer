import shutil
import os
import glob


def copy_vue_static():
    # Source and destination directories
    src_dir = os.path.join("casestrainer-vue", "dist")
    dest_dir = os.path.join("static", "vue")

    # Remove existing static files
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)

    # Create destination directory
    os.makedirs(dest_dir, exist_ok=True)

    # Copy all files from dist to static/vue
    for item in os.listdir(src_dir):
        s = os.path.join(src_dir, item)
        d = os.path.join(dest_dir, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)

    print(f"Copied Vue.js static files from {src_dir} to {dest_dir}")


if __name__ == "__main__":
    copy_vue_static()
