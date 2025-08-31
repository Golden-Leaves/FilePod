def format_file_size(file_size:int) -> str:
    """Converts a byte size into a human-readable format (e.g., 2.3 MB, 45.1 GB,...)."""
    size_map = {
    "B": 1,
    "KB": 1024,
    "MB": 1024**2,
    "GB": 1024**3,
    "TB": 1024**4,
    "PB": 1024**5,
}
    
    for size,bytes in reversed(list(size_map.items())):
        if file_size >= bytes: #If file_size is larger than current size unit
            return f"{file_size / bytes:.1f} {size}"
    return f"{file_size} B"
if __name__ == "__main__":
    print(format_file_size(1024*2))