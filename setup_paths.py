# setup_paths.py
import os
import re
import sys
from pathlib import Path

# This script updates the hardcoded project directory in .bat and .command files.

def update_script_paths():
    """
    Finds and updates the hardcoded PROJECT_DIR in shell scripts.
    """
    # The project directory is the directory containing this script.
    project_dir = Path(__file__).parent.resolve()
    
    # Prepare path strings for different script types
    # For .bat files, the path must be a valid string for the `re` module
    project_dir_bat = str(project_dir).replace('\\', '\\\\')
    # For .command files, the path should use forward slashes
    project_dir_unix = str(project_dir).replace('\\', '/')

    print(f"Project directory detected as: {project_dir_unix}\n")

    # Dynamically find all .bat and .command files in the project root
    script_paths = list(project_dir.glob("*.bat")) + list(project_dir.glob("*.command"))
    
    if not script_paths:
        print("No .bat or .command files found in the project root.")
        return

    update_count = 0
    
    for script_path in script_paths:
        script_name = script_path.name
        
        if not script_path.exists():
            print(f"Skipping: {script_name} (not found)")
            continue
            
        try:
            # Specify UTF-8 encoding to handle special characters
            content = script_path.read_text(encoding='utf-8')
            
            # Use regex to find and replace the PROJECT_DIR line
            if script_name.endswith('.bat'):
                # For .bat files: set PROJECT_DIR=...
                new_content, count = re.subn(
                    r'set PROJECT_DIR=.*', 
                    f'set PROJECT_DIR={project_dir_bat}', 
                    content
                )
            elif script_name.endswith('.command'):
                # For .command files: PROJECT_DIR="..."
                new_content, count = re.subn(
                    r'PROJECT_DIR=".*"', 
                    f'PROJECT_DIR="{project_dir_unix}"',
                    content
                )
            else:
                continue

            if count > 0:
                # Specify UTF-8 encoding for writing as well
                script_path.write_text(new_content, encoding='utf-8')
                print(f"Updated: {script_name}")
                update_count += 1
            else:
                print(f"No changes needed for: {script_name} (pattern not found)")

        except Exception as e:
            print(f"Error processing {script_name}: {e}", file=sys.stderr)
            
    if update_count > 0:
        print(f"\nSuccessfully updated {update_count} script(s).")
    else:
        print("\nNo scripts required updates.")

if __name__ == "__main__":
    update_script_paths()
