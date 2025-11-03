# move2doc.py

import os
import shutil
from pathlib import Path

def move_docs_to_folder():
    """Move all .md files except README.md to doc/ folder"""
    doc_folder = Path("doc")
    doc_folder.mkdir(exist_ok=True)

    # Find all .md files in root
    for md_file in Path(".").glob("*.md"):
        if md_file.name == "README.md":
            continue

        dest_path = doc_folder / md_file.name

        # Handle duplicates
        if dest_path.exists():
            base = dest_path.stem
            suffix = dest_path.suffix
            counter = 1
            while dest_path.exists():
                dest_path = doc_folder / f"{base}_{counter}{suffix}"
                counter += 1

        print(f"Moving {md_file} to {dest_path}")
        shutil.move(str(md_file), str(dest_path))

    print("Documentation organization complete!")

if __name__ == "__main__":
    move_docs_to_folder()
