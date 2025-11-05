#!/usr/bin/env python3
"""
Phase 1 Verification Script
Checks if all Phase 1 requirements are met and tracks repeated issues
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import hashlib

# Counter file for tracking repeated issues
COUNTER_FILE = "doc/phase1counter.md"
TODO_FILE = "doc/todo_list.md"
CHECKLIST_FILE = "doc/PHASE1_CHECKLIST.md"

class Phase1Verifier:
    def __init__(self):
        self.issues = []
        self.counters = self.load_counters()
        self.all_checks_passed = True
    
    def load_counters(self):
        """Load existing counters from file"""
        counters = {}
        if os.path.exists(COUNTER_FILE):
            try:
                with open(COUNTER_FILE, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip() and '|' in line and not line.startswith('|---'):
                            parts = line.strip().split('|')
                            if len(parts) >= 4:
                                issue_hash = parts[1].strip()
                                count = parts[2].strip()
                                try:
                                    counters[issue_hash] = int(count)
                                except ValueError:
                                    pass
            except Exception as e:
                print(f"Warning: Could not read counter file: {e}")
        return counters
    
    def save_counters(self):
        """Save counters to file with timestamp"""
        os.makedirs("doc", exist_ok=True)
        
        with open(COUNTER_FILE, 'w', encoding='utf-8') as f:
            f.write("# Phase 1 Issue Counter\n\n")
            f.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("| Issue Hash | Count | First Seen | Last Seen | Issue Description |\n")
            f.write("|------------|-------|------------|-----------|-------------------|\n")
            
            for issue_hash, count in sorted(self.counters.items(), key=lambda x: x[1], reverse=True):
                # Find the issue description from current issues
                description = "Unknown"
                for issue in self.issues:
                    if self.hash_issue(issue) == issue_hash:
                        description = issue[:60] + "..." if len(issue) > 60 else issue
                        break
                
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"| {issue_hash} | {count} | - | {timestamp} | {description} |\n")
            
            f.write(f"\n**Total unique issues: {len(self.counters)}**\n")
            f.write(f"**Total occurrences: {sum(self.counters.values())}**\n")
    
    def hash_issue(self, issue):
        """Create a hash for an issue to track it"""
        return hashlib.md5(issue.encode()).hexdigest()[:8]
    
    def log_issue(self, issue):
        """Log an issue and increment its counter"""
        self.issues.append(issue)
        issue_hash = self.hash_issue(issue)
        self.counters[issue_hash] = self.counters.get(issue_hash, 0) + 1
        self.all_checks_passed = False
    
    def check_required_files(self):
        """Check if all required files from Phase 1 exist"""
        print("=" * 70)
        print("PHASE 1 VERIFICATION - File Structure Check")
        print("=" * 70)
        
        required_files = {
            # Part A: Project Structure
            "doc/": "Directory for documentation",
            "test/": "Directory for tests",
            "asset/sound/": "Directory for sound effects",
            "asset/music/": "Directory for music files",
            "asset/sprite/game/": "Directory for game sprites",
            
            # Part A.2: Utility script
            "move2doc.py": "Utility to move files to correct directories",
            
            # Part A.3: Updated config
            "config.py": "Global configuration file",
            
            # Part B: Asset Management
            "asset/asset_loader.py": "Asset loading system with DEBUG support",
            
            # Part C: Rendering System
            "rendering/renderer.py": "Pygame-based rendering system",
            
            # Part D: Requirements
            "requirements.txt": "Python dependencies (should contain pygame)",
            
            # Part F: Animation System
            "rendering/animation.py": "Ping-pong animation system",
            
            # Part G: Testing
            "test/test_migration_phase1.py": "Phase 1 unit tests",
            
            # Part H: Documentation
            "doc/PHASE1_CHECKLIST.md": "Phase 1 completion checklist",
            "doc/todo_list.md": "Detailed Phase 1 plan"
        }
        
        missing_files = []
        
        for filepath, description in required_files.items():
            path = Path(filepath)
            exists = path.exists()
            
            status = "✓" if exists else "✗"
            print(f"{status} {filepath:<40} - {description}")
            
            if not exists:
                missing_files.append((filepath, description))
        
        if missing_files:
            print("\n" + "!" * 70)
            print("MISSING FILES DETECTED")
            print("!" * 70)
            
            for filepath, description in missing_files:
                issue = f"Missing file: {filepath} ({description})"
                self.log_issue(issue)
                
                print(f"\n❌ Missing: {filepath}")
                print(f"   Purpose: {description}")
                print(f"\n   📋 ACTION REQUIRED:")
                print(f"   1. Open '{TODO_FILE}'")
                print(f"   2. Find the section that creates '{filepath}'")
                print(f"   3. Follow ALL instructions in that section COMPLETELY")
                print(f"   4. Verify the file is created before running phase1.py again")
                print(f"\n   Example of what's missing:")
                print(f"   {self.get_file_example(filepath)}")
                print("-" * 70)
            
            return False
        
        print("\n✅ All required files are present!")
        return True
    
    def get_file_example(self, filepath):
        """Provide an example of what the missing file should contain"""
        examples = {
            "move2doc.py": """
import os
import shutil
from pathlib import Path

def move_files():
    # Move markdown files to doc/
    # Move test files to test/
    ...
""",
            "config.py": """
# Global configuration
DEBUG = True
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
...
""",
            "asset/asset_loader.py": """
import pygame
from config import DEBUG

class AssetLoader:
    def load_sprite(self, path, scale=1.0):
        # Load sprite with DEBUG fallback
        ...
""",
            "rendering/renderer.py": """
import pygame
from config import WINDOW_WIDTH, WINDOW_HEIGHT

class Renderer:
    def __init__(self):
        pygame.init()
        ...
""",
            "rendering/animation.py": """
import pygame

class Animation:
    def __init__(self, sprites, fps=10):
        # Ping-pong animation system
        ...
""",
            "requirements.txt": """
pygame==2.5.2
""",
            "test/test_migration_phase1.py": """
import unittest

class TestPhase1Setup(unittest.TestCase):
    def test_directory_structure(self):
        ...
""",
            "doc/PHASE1_CHECKLIST.md": """
# Phase 1 Migration Checklist

## Pre-Migration
- [ ] Backup entire project
- [ ] Commit current state to git
...
"""
        }
        
        return examples.get(filepath, "   (See doc/todo_list.md for complete implementation)")
    
    def check_checklist_items(self):
        """Check PHASE1_CHECKLIST.md for unchecked items"""
        print("\n" + "=" * 70)
        print("PHASE 1 VERIFICATION - Checklist Progress")
        print("=" * 70)
        
        if not os.path.exists(CHECKLIST_FILE):
            issue = f"Checklist file not found: {CHECKLIST_FILE}"
            self.log_issue(issue)
            print(f"❌ {issue}")
            return False
        
        try:
            with open(CHECKLIST_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            issue = f"Could not read checklist file: {e}"
            self.log_issue(issue)
            print(f"❌ {issue}")
            return False
        
        lines = content.split('\n')
        unchecked_items = []
        checked_items = []
        current_section = "Unknown"
        
        for line in lines:
            # Track current section
            if line.startswith('##'):
                current_section = line.strip('# ').strip()
            
            # Check for checkbox items
            if '- [ ]' in line:
                item = line.split('- [ ]')[1].strip()
                unchecked_items.append((current_section, item))
            elif '- [x]' in line or '- [X]' in line:
                item = line.split('- [')[1].split(']')[1].strip()
                checked_items.append((current_section, item))
        
        total_items = len(checked_items) + len(unchecked_items)
        progress = len(checked_items) / total_items * 100 if total_items > 0 else 0
        
        print(f"\n📊 Progress: {len(checked_items)}/{total_items} items completed ({progress:.1f}%)")
        print(f"✅ Completed: {len(checked_items)}")
        print(f"⏳ Remaining: {len(unchecked_items)}")
        
        if unchecked_items:
            print("\n" + "!" * 70)
            print("UNCOMPLETED CHECKLIST ITEMS")
            print("!" * 70)
            
            # Group by section
            sections = {}
            for section, item in unchecked_items:
                if section not in sections:
                    sections[section] = []
                sections[section].append(item)
            
            for section, items in sections.items():
                print(f"\n📌 Section: {section}")
                for item in items:
                    print(f"   ⏳ {item}")
                    
                    issue = f"Unchecked: [{section}] {item}"
                    self.log_issue(issue)
            
            print("\n" + "!" * 70)
            print("📋 ACTION REQUIRED:")
            print("!" * 70)
            print(f"\n1. Open '{TODO_FILE}'")
            print(f"2. Open '{CHECKLIST_FILE}'")
            print(f"3. For each unchecked item above:")
            print(f"   - Find the corresponding section in {TODO_FILE}")
            print(f"   - Complete ALL steps in that section")
            print(f"   - Verify the implementation works")
            print(f"   - Check the box in {CHECKLIST_FILE} (change [ ] to [x])")
            print(f"4. Run phase1.py again to verify\n")
            
            return False
        
        print("\n✅ All checklist items are completed!")
        return True
    
    def check_requirements_content(self):
        """Verify requirements.txt contains pygame and not tcod"""
        print("\n" + "=" * 70)
        print("PHASE 1 VERIFICATION - Dependencies Check")
        print("=" * 70)
        
        if not os.path.exists("requirements.txt"):
            return True  # Already caught in file check
        
        try:
            with open("requirements.txt", 'r', encoding='utf-8') as f:
                content = f.read().lower()
        except Exception as e:
            issue = f"Could not read requirements.txt: {e}"
            self.log_issue(issue)
            print(f"❌ {issue}")
            return False
        
        has_pygame = 'pygame' in content
        has_tcod = 'tcod' in content or 'libtcod' in content
        
        print(f"{'✓' if has_pygame else '✗'} pygame present: {has_pygame}")
        print(f"{'✓' if not has_tcod else '✗'} tcod removed: {not has_tcod}")
        
        if not has_pygame:
            issue = "requirements.txt missing pygame dependency"
            self.log_issue(issue)
            print(f"\n❌ {issue}")
            print(f"   Add 'pygame==2.5.2' to requirements.txt")
            return False
        
        if has_tcod:
            issue = "requirements.txt still contains tcod dependencies"
            self.log_issue(issue)
            print(f"\n❌ {issue}")
            print(f"   Remove all tcod/libtcod entries from requirements.txt")
            return False
        
        print("\n✅ Dependencies are correct!")
        return True
    
    def check_for_tcod_imports(self):
        """Check new files don't import tcod"""
        print("\n" + "=" * 70)
        print("PHASE 1 VERIFICATION - TCOD Import Check")
        print("=" * 70)
        
        files_to_check = [
            "config.py",
            "asset/asset_loader.py",
            "rendering/renderer.py",
            "rendering/animation.py"
        ]
        
        tcod_imports_found = []
        
        for filepath in files_to_check:
            if not os.path.exists(filepath):
                continue
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Only check actual import statements (not comments, docstrings, or examples)
                import_lines = []
                in_docstring = False
                docstring_delimiter = None
                
                for line_num, line in enumerate(lines, 1):
                    stripped = line.strip()
                    
                    # Skip empty lines
                    if not stripped:
                        continue
                    
                    # Track docstrings (triple quotes)
                    if '"""' in stripped or "'''" in stripped:
                        if '"""' in stripped:
                            if not in_docstring:
                                in_docstring = True
                                docstring_delimiter = '"""'
                            elif docstring_delimiter == '"""':
                                in_docstring = False
                                docstring_delimiter = None
                        elif "'''" in stripped:
                            if not in_docstring:
                                in_docstring = True
                                docstring_delimiter = "'''"
                            elif docstring_delimiter == "'''":
                                in_docstring = False
                                docstring_delimiter = None
                        continue
                    
                    # Skip lines in docstrings
                    if in_docstring:
                        continue
                    
                    # Skip comment-only lines
                    if stripped.startswith('#'):
                        continue
                    
                    # Check if line contains actual TCOD import
                    # Only flag if it's an import statement, not a comment or example
                    if ('import libtcod' in stripped or 
                        'from libtcod' in stripped or 
                        ('import tcod' in stripped and 'tcodpy' not in stripped) or
                        ('from tcod' in stripped and 'tcodpy' not in stripped)):
                        import_lines.append((line_num, line.strip()))
                
                if import_lines:
                    tcod_imports_found.append(filepath)
                    print(f"✗ {filepath} - Contains tcod imports")
                    for line_num, line in import_lines:
                        print(f"   Line {line_num}: {line}")
                else:
                    print(f"✓ {filepath} - No tcod imports")
            except Exception as e:
                print(f"⚠ {filepath} - Could not check: {e}")
        
        if tcod_imports_found:
            print("\n" + "!" * 70)
            print("TCOD IMPORTS DETECTED IN NEW FILES")
            print("!" * 70)
            
            for filepath in tcod_imports_found:
                issue = f"TCOD imports found in: {filepath}"
                self.log_issue(issue)
                print(f"\n❌ {filepath}")
                print(f"   These files should NOT import tcod")
                print(f"   Replace with Pygame equivalents")
                print(f"   See {TODO_FILE} for correct implementations")
            
            return False
        
        print("\n✅ No tcod imports in new files!")
        return True
    
    def show_counter_summary(self):
        """Display summary of repeated issues"""
        if not self.counters:
            return
        
        print("\n" + "=" * 70)
        print("ISSUE FREQUENCY ANALYSIS")
        print("=" * 70)
        
        # Sort by count
        sorted_issues = sorted(self.counters.items(), key=lambda x: x[1], reverse=True)
        
        print(f"\nTop repeated issues (see {COUNTER_FILE} for details):")
        for i, (issue_hash, count) in enumerate(sorted_issues[:5], 1):
            # Find description
            description = "Unknown"
            for issue in self.issues:
                if self.hash_issue(issue) == issue_hash:
                    description = issue
                    break
            
            print(f"\n{i}. [{issue_hash}] Count: {count}")
            print(f"   {description[:60]}{'...' if len(description) > 60 else ''}")
        
        if sum(self.counters.values()) > 10:
            print("\n⚠️  WARNING: Some issues have been detected multiple times!")
            print("   This might indicate:")
            print("   - Instructions in todo_list.md are unclear")
            print("   - Steps are being skipped")
            print("   - Files are being created incorrectly")
            print(f"\n   Review {COUNTER_FILE} for detailed frequency analysis")
    
    def run(self):
        """Run all verification checks"""
        print("\n" + "=" * 70)
        print("🔍 PHASE 1 VERIFICATION STARTING")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Run all checks
        files_ok = self.check_required_files()
        deps_ok = self.check_requirements_content()
        imports_ok = self.check_for_tcod_imports()
        checklist_ok = self.check_checklist_items()
        
        # Save counters after all checks
        self.save_counters()
        
        # Show counter summary if there are issues
        if not self.all_checks_passed:
            self.show_counter_summary()
        
        # Final summary
        print("\n" + "=" * 70)
        print("VERIFICATION SUMMARY")
        print("=" * 70)
        
        checks = [
            ("File Structure", files_ok),
            ("Dependencies", deps_ok),
            ("TCOD Imports", imports_ok),
            ("Checklist Progress", checklist_ok)
        ]
        
        for check_name, passed in checks:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} - {check_name}")
        
        if self.all_checks_passed:
            print("\n" + "🎉" * 35)
            print("✅ PHASE 1 VERIFICATION COMPLETE!")
            print("🎉" * 35)
            print("\n✨ All requirements met! Ready for Phase 2.")
            print(f"\nNext steps:")
            print(f"1. Review the implementation")
            print(f"2. Run tests: python -m pytest test/test_migration_phase1.py")
            print(f"3. Run tests: `timeout 5s python battle.py 0`")
            print(f"4. Run tests: `timeout 5s python scenario.py`")
            print(f"5. Proceed to Phase 2 planning\n")
            return 0
        else:
            print("\n" + "⚠️ " * 35)
            print("❌ PHASE 1 VERIFICATION FAILED")
            print("⚠️ " * 35)
            print(f"\n📝 {len(self.issues)} issue(s) found")
            print(f"📊 Issue frequency logged to: {COUNTER_FILE}")
            print(f"\n⚡ Quick fix:")
            print(f"   1. Address the issues listed above")
            print(f"   2. Follow {TODO_FILE} carefully")
            print(f"   3. Run phase1.py again to verify\n")
            return 1


def main():
    """Main entry point"""
    verifier = Phase1Verifier()
    return verifier.run()


if __name__ == "__main__":
    sys.exit(main())
