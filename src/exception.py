#!/usr/bin/env python3
import os
import subprocess
import sys
from datetime import datetime, timedelta
import random
import shutil
import json

ASCII_ART = """
       ____   ___   _____            ____   _   _   _____      _      _____ 
      / ___| |_ _| |_   _|          / ___| | | | | | ____|    / \    |_   _|
     | |  _   | |    | |    _____  | |     | |_| | |  _|     / _ \     | |  
     | |_| |  | |    | |   |_____| | |___  |  _  | | |___   / ___ \    | |  
      \____| |___|   |_|            \____| |_| |_| |_____| /_/   \_\   |_|  
"""

def run_command(command, description="", ignore_error=False):
    """Execute shell command and handle errors"""
    if description:
        print(f"\n{description}...")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout.strip())
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr if e.stderr else e.stdout}")
        if not ignore_error:
            sys.exit(1)
        return False


def clone_repository(repo_url, repo_name):
    """Clone repository as bare repository with auto-cleanup"""
    if os.path.exists(repo_name):
        print(f"\n⚠️  Directory '{repo_name}' already exists. Cleaning up...")
        shutil.rmtree(repo_name)
        print(f"✓ Cleaned up existing directory")
    
    return run_command(
        f"git clone --bare {repo_url} {repo_name}",
        "Cloning the repository"
    )


def get_commit_list(repo_path):
    """Get list of all commit hashes"""
    os.chdir(repo_path)
    try:
        result = subprocess.run(
            "git rev-list --all --reverse",
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        commits = result.stdout.strip().split('\n')
        os.chdir("..")
        return [c for c in commits if c]
    except:
        os.chdir("..")
        return []


def modify_history(repo_name, new_author_name, new_author_email, 
                   modify_dates=False, start_date=None, end_date=None,
                   replace_text=False, old_text=None, new_text=None):
    """
    Modify git history with evenly distributed dates
    Uses git filter-branch with index-based date calculation
    """
    repo_path = os.path.abspath(repo_name)
    
    # Get commit list for distribution
    if modify_dates:
        commit_list = get_commit_list(repo_path)
        commit_count = len(commit_list)
        print(f"\n📊 Total commits: {commit_count}")
        
        if commit_count > 0 and start_date and end_date:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            total_days = (end_dt - start_dt).days + 1
            
            print(f"📅 Date range: {total_days} days")
            print(f"⚖️  Distribution: ~{commit_count / total_days:.1f} commits per day")
            
            # Create commit hash to index mapping
            commit_mapping = {commit_list[i]: i for i in range(len(commit_list))}
            
            # Save mapping to temp file
            mapping_file = os.path.join(repo_path, 'commit_mapping.json')
            with open(mapping_file, 'w') as f:
                json.dump({
                    'commits': commit_mapping,
                    'total': commit_count,
                    'start_date': start_date,
                    'end_date': end_date
                }, f)
    
    os.chdir(repo_path)
    print("\nModifying commit history...")
    
    if modify_dates and start_date and end_date:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        # Create shell script for date calculation
        date_script = f'''#!/bin/bash

# Load commit mapping
MAPPING_FILE="{repo_path}/commit_mapping.json"
COMMIT_HASH=$GIT_COMMIT

# Get total commits
TOTAL_COMMITS=$(grep -o '"total": [0-9]*' "$MAPPING_FILE" | cut -d ' ' -f 2)

# Get commit index (simple counter)
if [ ! -f /tmp/git_commit_counter ]; then
    echo "0" > /tmp/git_commit_counter
fi
COMMIT_INDEX=$(cat /tmp/git_commit_counter)
echo $((COMMIT_INDEX + 1)) > /tmp/git_commit_counter

# Calculate dates
START_TIMESTAMP={int(start_dt.timestamp())}
END_TIMESTAMP={int(end_dt.timestamp())}
TOTAL_SECONDS=$((END_TIMESTAMP - START_TIMESTAMP))

# Calculate seconds per commit
if [ "$TOTAL_COMMITS" -gt 0 ]; then
    SECONDS_PER_COMMIT=$((TOTAL_SECONDS / TOTAL_COMMITS))
else
    SECONDS_PER_COMMIT=0
fi

# Calculate this commit's base timestamp
COMMIT_OFFSET=$((COMMIT_INDEX * SECONDS_PER_COMMIT))

# Add randomness (±2 hours = ±7200 seconds)
RANDOM_OFFSET=$((RANDOM % 14400 - 7200))

# Final timestamp
NEW_TIMESTAMP=$((START_TIMESTAMP + COMMIT_OFFSET + RANDOM_OFFSET))

# Export with new author and date
export GIT_AUTHOR_NAME="{new_author_name}"
export GIT_AUTHOR_EMAIL="{new_author_email}"
export GIT_COMMITTER_NAME="{new_author_name}"
export GIT_COMMITTER_EMAIL="{new_author_email}"
export GIT_AUTHOR_DATE="$NEW_TIMESTAMP +0530"
export GIT_COMMITTER_DATE="$NEW_TIMESTAMP +0530"
'''
        
        # Write shell script
        script_path = os.path.join(repo_path, 'set_dates.sh')
        with open(script_path, 'w') as f:
            f.write(date_script)
        os.chmod(script_path, 0o755)
        
        # Reset counter
        subprocess.run("echo '0' > /tmp/git_commit_counter", shell=True)
        
        # Run git filter-branch
        filter_command = f'git filter-branch -f --env-filter "source {script_path}" --tag-name-filter cat -- --branches --tags'
        
        run_command(filter_command, "Applying evenly distributed dates")
        
        # Cleanup
        if os.path.exists(script_path):
            os.remove(script_path)
        if os.path.exists(mapping_file):
            os.remove(mapping_file)
        subprocess.run("rm -f /tmp/git_commit_counter", shell=True)
        
    else:
        # Simple author change without dates
        filter_command = f'''git filter-branch -f --env-filter '
export GIT_AUTHOR_NAME="{new_author_name}"
export GIT_AUTHOR_EMAIL="{new_author_email}"
export GIT_COMMITTER_NAME="{new_author_name}"
export GIT_COMMITTER_EMAIL="{new_author_email}"
' --tag-name-filter cat -- --branches --tags
'''
        run_command(filter_command, "Applying author changes")
    
    # Text replacement
    if replace_text and old_text and new_text:
        old_escaped = old_text.replace('/', '\\/')
        new_escaped = new_text.replace('/', '\\/')
        msg_filter = f"git filter-branch -f --msg-filter 'sed \"s/{old_escaped}/{new_escaped}/g\"' -- --all"
        run_command(msg_filter, "Replacing text in commit messages")
    
    # Cleanup
    run_command("git reflog expire --expire=now --all", ignore_error=True)
    run_command("git gc --prune=now --aggressive", "Cleaning up repository")
    
    os.chdir("..")


def push_to_new_repository(repo_name, new_repo_url):
    """Push modified repository to new remote"""
    repo_path = os.path.abspath(repo_name)
    os.chdir(repo_path)
    
    run_command(
        f"git remote set-url origin {new_repo_url}",
        "Setting new remote repository"
    )
    
    run_command(
        "git push --mirror",
        "Pushing to new repository"
    )
    
    os.chdir("..")


def cleanup(repo_name):
    """Remove temporary repository directory"""
    if os.path.exists(repo_name):
        shutil.rmtree(repo_name)
        print(f"\n✓ Cleaned up temporary directory: {repo_name}")


def main():
    """Main execution function"""
    print(ASCII_ART)
    
    work_dir = os.path.expanduser("~/Desktop/git-transfer")
    os.makedirs(work_dir, exist_ok=True)
    original_dir = os.getcwd()
    os.chdir(work_dir)
    
    print(f"📁 Working directory: {work_dir}")
    print("=" * 50)
    
    try:
        old_repo_url = input("Enter the URL of the old repository: ").strip()
        if not old_repo_url:
            print("Error: Repository URL cannot be empty!")
            sys.exit(1)
        
        new_repo_url = input("Enter the URL of the new repository: ").strip()
        if not new_repo_url:
            print("Error: New repository URL cannot be empty!")
            sys.exit(1)
        
        new_author_name = input("Enter the new author's name: ").strip()
        if not new_author_name:
            print("Error: Author name cannot be empty!")
            sys.exit(1)
        
        new_author_email = input("Enter the new author's email: ").strip()
        if not new_author_email:
            print("Error: Author email cannot be empty!")
            sys.exit(1)
        
        modify_dates = input("Do you want to modify commit dates? (yes/no): ").strip().lower() == 'yes'
        start_date = None
        end_date = None
        start_date_str = None
        end_date_str = None
        
        if modify_dates:
            print("Enter the date range for randomizing commit dates:")
            start_date_str = input("Enter start date (YYYY-MM-DD): ").strip()
            end_date_str = input("Enter end date (YYYY-MM-DD): ").strip()
            
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                
                if start_date > end_date:
                    print("Error: Start date must be before end date!")
                    sys.exit(1)
            except ValueError:
                print("Error: Invalid date format! Use YYYY-MM-DD")
                sys.exit(1)
        
        replace_text = input("Do you want to replace text in commit messages? (yes/no): ").strip().lower() == 'yes'
        old_text = None
        new_text = None
        
        if replace_text:
            old_text = input("Enter text to replace: ").strip()
            new_text = input("Enter replacement text: ").strip()
        
        print("\n" + "=" * 50)
        print("TRANSFER SUMMARY:")
        print(f"Old repository: {old_repo_url}")
        print(f"New repository: {new_repo_url}")
        print(f"New author: {new_author_name} <{new_author_email}>")
        if modify_dates:
            print(f"Date range: {start_date_str} to {end_date_str}")
            print("Distribution: Evenly spread across date range")
        if replace_text:
            print(f"Text replacement: '{old_text}' → '{new_text}'")
        print("=" * 50)
        
        confirm = input("Proceed with transfer? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Transfer cancelled.")
            sys.exit(0)
        
        repo_name = old_repo_url.split('/')[-1].replace('.git', '') + '.git'
        
        clone_repository(old_repo_url, repo_name)
        
        modify_history(
            repo_name,
            new_author_name,
            new_author_email,
            modify_dates,
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None,
            replace_text,
            old_text,
            new_text
        )
        
        push_to_new_repository(repo_name, new_repo_url)
        
        cleanup(repo_name)
        
        print("\n" + "=" * 50)
        print("✓ Transfer completed successfully!")
        print("=" * 50)
        print(f"\nYou can now clone from: {new_repo_url}")
        print(f"Temporary files location: {work_dir}")
        print("You can safely delete the git-transfer folder from Desktop.")
        
    except KeyboardInterrupt:
        print("\n\nTransfer cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        os.chdir(original_dir)


if __name__ == "__main__":
    main()