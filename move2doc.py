import os
import shutil
from pathlib import Path

def move_files():
    """Move documentation and test files to proper directories"""
    root = Path('.')

    # Move markdown files (except README.md) to doc/
    for md_file in root.glob('*.md'):
        if md_file.name != 'README.md':
            dest = Path('doc') / md_file.name
            if dest.exists():
                # Rename if duplicate
                base = dest.stem
                ext = dest.suffix
                counter = 1
                while dest.exists():
                    dest = Path('doc') / f"{base}_{counter}{ext}"
                    counter += 1
            shutil.move(str(md_file), str(dest))
            print(f"Moved {md_file.name} to {dest}")

    # Move test files to test/
    for test_file in root.glob('*test*.py'):
        dest = Path('test') / test_file.name
        if dest.exists():
            base = dest.stem
            ext = dest.suffix
            counter = 1
            while dest.exists():
                dest = Path('test') / f"{base}_{counter}{ext}"
                counter += 1
        shutil.move(str(test_file), str(dest))
        print(f"Moved {test_file.name} to {dest}")

if __name__ == '__main__':
    move_files()
