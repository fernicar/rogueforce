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
COUNTER_FILE = "doc/phasecounter.md"
TODO_FILE = "doc/todo_list.md"
CHECKLIST_FILE = "doc/PHASE_CHECKLIST.md"

class PhaseVerifier:
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

        # Note: Based on the new codebase structure, the root asset folder is 'assets/'
        required_files = {
            # Part A: Project Structure
            "doc/": "Directory for documentation",
            "rendering/": "Directory for rendering components",
            "assets/sprite/": "Directory for game sprites",

            # Part B: Asset Management
            "assets/asset_loader.py": "Asset loading system with DEBUG support",

            # Part C: Rendering System
            "rendering/renderer.py": "Pygame-based rendering system",

            # Part D: Requirements
            "requirements.txt": "Python dependencies (should contain pygame)",

            # Part F: Animation System
            "rendering/animation.py": "Ping-pong animation system",

            # Part H: Documentation
            "doc/PHASE_CHECKLIST.md": "Phase 1 completion checklist",
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
                print(f"   2. Find the section that creates or modifies '{filepath}'")
                print(f"   3. Follow ALL instructions in that section COMPLETELY. Do not skip any steps.")
                print(f"   4. Verify the file is created before running this script again.")
                print(f"\n   Example of what's missing:")
                print(f"   {self.get_file_example(filepath)}")
                print("-" * 70)

            return False

        print("\n✅ All required files are present!")
        return True

    def get_file_example(self, filepath):
        """Provide an example of what the missing file should contain"""
        examples = {
            "config.py": """
# Global configuration
DEBUG = True
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
...
""",
            "assets/asset_loader.py": """
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
            "doc/PHASE_CHECKLIST.md": """
# Phase 1 Migration Checklist

## Pre-Migration
- [ ] Backup entire project
- [ ] Commit current state to git
...
"""
        }

        return examples.get(filepath, f"   (See {TODO_FILE} for the complete implementation details)")

    def check_checklist_items(self):
        """Check PHASE_CHECKLIST.md for unchecked items"""
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
            print(f"   - Find the corresponding section in '{TODO_FILE}'")
            print(f"   - Complete ALL steps for that item")
            print(f"   - Verify the implementation works as described")
            print(f"   - Only then, check the box in '{CHECKLIST_FILE}' (change [ ] to [x])")
            print(f"4. Run this script again to verify your changes.\n")

            return False

        print("\n✅ All checklist items are completed!")
        return True
    
    def check_requirements_content(self):
        """Verify requirements.txt contains pygame and not tcod"""
        print("\n" + "=" * 70)
        print("PHASE 1 VERIFICATION - Dependencies Check")
        print("=" * 70)

        if not os.path.exists("requirements.txt"):
            return True # Already caught in file check

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
            print(f"  Add 'pygame==2.5.2' to requirements.txt")
            return False

        if has_tcod:
            issue = "requirements.txt still contains tcod dependencies"
            self.log_issue(issue)
            print(f"\n❌ {issue}")
            print(f"  Remove all tcod/libtcod entries from requirements.txt")
            return False

        print("\n✅ Dependencies are correct!")
        return True

    def show_counter_summary(self):
        """Display summary of repeated issues"""
        if not self.counters:
            return

        print("\n" + "=" * 70)
        print("ISSUE FREQUENCY ANALYSIS")
        print("=" * 70)

        sorted_issues = sorted(self.counters.items(), key=lambda x: x[1], reverse=True)

        print(f"\nTop repeated issues (see '{COUNTER_FILE}' for full details):")
        for i, (issue_hash, count) in enumerate(sorted_issues[:5], 1):
            description = "Unknown"
            for issue in self.issues:
                if self.hash_issue(issue) == issue_hash:
                    description = issue
                    break

            print(f"\n{i}. [{issue_hash}] Count: {count}")
            print(f"   {description[:60]}{'...' if len(description) > 60 else ''}")

        if sum(self.counters.values()) > 5:
            print("\n⚠️  WARNING: Some issues have been detected multiple times!")
            print("   This might indicate steps in 'doc/todo_list.md' are being skipped or misunderstood.")
            print(f"   Please review the instructions for the issues listed above very carefully.")
            print(f"   See '{COUNTER_FILE}' for a detailed frequency analysis.")

    def run(self):
        """Run all verification checks"""
        print("\n" + "=" * 70)
        print("🔍 PHASE 1 VERIFICATION STARTING")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        files_ok = self.check_required_files()
        # Only check checklist and dependencies if files are present
        checklist_ok = self.check_checklist_items() if files_ok else False
        deps_ok = self.check_requirements_content() if files_ok else False
        
        self.save_counters()

        if not self.all_checks_passed:
            self.show_counter_summary()

        print("\n" + "=" * 70)
        print("VERIFICATION SUMMARY")
        print("=" * 70)

        checks = [
            ("File Structure", files_ok),
            ("Dependencies", deps_ok),
            ("Checklist Progress", checklist_ok)
        ]

        for check_name, passed in checks:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} - {check_name}")

        if self.all_checks_passed:
            print("\n" + "🎉" * 35)
            print("✅ PHASE 1 VERIFICATION COMPLETE!")
            print("🎉" * 35)
            print("\n✨ All requirements met! You are ready to proceed.")
            print(f"\nNext steps:")
            print(f"1. Commit your changes to version control.")
            print(f"2. Proceed to the next phase of the plan.\n")
            return 0
        else:
            print("\n" + "⚠️ " * 35)
            print("❌ PHASE 1 VERIFICATION FAILED")
            print("⚠️ " * 35)
            print(f"\n📝 {len(self.issues)} issue(s) found.")
            print(f"📊 Issue frequency has been logged to: {COUNTER_FILE}")
            print(f"\n⚡ Quick fix:")
            print(f"   1. Carefully address the issues listed above.")
            print(f"   2. Follow the instructions in '{TODO_FILE}' precisely.")
            print(f"   3. Run this script again to verify.\n")
            return 1


def main():
    """Main entry point"""
    verifier = PhaseVerifier()
    return verifier.run()


if __name__ == "__main__":
    sys.exit(main())