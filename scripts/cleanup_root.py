
import os
import shutil
import time

def cleanup_root():
    root_dir = r"C:\GenModels\[Antigravity]\projects\test1"
    trash_dir = os.path.join(root_dir, "_trash")
    keep_dirs = ["davinci-resolve-mcp", "_trash"]
    
    if not os.path.exists(trash_dir):
        os.makedirs(trash_dir)
        print(f"Created {trash_dir}")

    print(f"Cleaning {root_dir}...")
    
    # List everything
    items = os.listdir(root_dir)
    count = 0
    for item in items:
        if item in keep_dirs:
            continue
            
        src_path = os.path.join(root_dir, item)
        dst_path = os.path.join(trash_dir, item)
        
        try:
            # Handle collision
            if os.path.exists(dst_path):
                base, ext = os.path.splitext(item)
                dst_path = os.path.join(trash_dir, f"{base}_{int(time.time())}{ext}")
            
            shutil.move(src_path, dst_path)
            print(f"Moved: {item}")
            count += 1
        except Exception as e:
            print(f"Failed to move {item}: {e}")
            
    print(f"Cleanup complete. Moved {count} items.")

if __name__ == "__main__":
    cleanup_root()
