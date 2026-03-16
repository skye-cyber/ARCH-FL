import os


def get_folder_size(folder_path):
    total_size = 0
    if not (os.path.exists(folder_path)):
        return 0

    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if not os.path.islink(file_path):
                try:
                    total_size += os.path.getsize(file_path)
                except OSError:
                    pass  # Skip inaccessible files
    return total_size


def format_size(size_bytes):
    for unit in ["bytes", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"
