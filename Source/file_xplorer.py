import os
import sys
import subprocess
import platform
from pathlib import Path
import msvcrt  # For Windows
import tempfile
import shutil

# Cross-platform getch implementation
def getch():
    if os.name == 'nt':
        return msvcrt.getch().decode('utf-8')
    else:
        import tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def list_files(directory):
    """List all files and directories in the given directory."""
    try:
        items = os.listdir(directory)
        files = []
        dirs = []
        
        for item in items:
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path):
                dirs.append(f"[D] {item}")
            else:
                files.append(f"[F] {item}")
        
        return dirs + files, len(dirs + files)
    except PermissionError:
        return ["[Error] Permission denied"], 0
    except Exception as e:
        return [f"[Error] {str(e)}"], 0

def run_python_file(file_path):
    """Run a Python script."""
    try:
        subprocess.run([sys.executable, file_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running script: {e}")
    input("\nPress Enter to continue...")

def run_shell_script(file_path):
    """Run a shell script."""
    try:
        if platform.system() == 'Windows':
            print("Warning: Shell script execution on Windows may not work as expected.")
            subprocess.run([file_path], shell=True, check=True)
        else:
            subprocess.run(['bash', file_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running script: {e}")
    input("\nPress Enter to continue...")

def edit_file(file_path):
    """Simple text editor for Python files."""
    try:
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create a temporary file for editing
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False, encoding='utf-8') as temp_file:
            temp_path = temp_file.name
            temp_file.write(content)
        
        # Open the default editor (on Windows) or use nano/vi on Unix
        if os.name == 'nt':
            # On Windows, try to use the default editor
            os.system(f'notepad "{temp_path}"')
        else:
            # On Unix-like systems, try nano first, then vi
            editor = 'nano' if shutil.which('nano') else 'vi'
            os.system(f'{editor} "{temp_path}"')
        
        # Ask if user wants to save changes
        if input("\nSave changes? (y/n): ").lower() == 'y':
            # Backup the original file
            backup_path = f"{file_path}.bak"
            if os.path.exists(backup_path):
                os.remove(backup_path)
            os.rename(file_path, backup_path)
            
            # Copy the edited file back to the original location
            shutil.copy2(temp_path, file_path)
            print(f"Changes saved to {file_path}")
            print(f"Original file backed up as {backup_path}")
        
        # Clean up the temporary file
        os.unlink(temp_path)
        
    except Exception as e:
        print(f"Error editing file: {e}")
    
    input("\nPress any key to continue...")

def install_requirements(file_path):
    """Install requirements from requirements.txt."""
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        input("\nPress any key to continue...")
        return
    
    print(f"Installing requirements from {file_path}...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', file_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")
    input("\nPress any key to continue...")

def main():
    current_dir = os.getcwd()
    selected_idx = 0
    
    while True:
        clear_screen()
        print(f"File Explorer - {current_dir}\n")
        print("Navigation: ↑/↓ to move | → to enter | ← to go back | Enter to select | q to quit\n")
        
        files, count = list_files(current_dir)
        
        if count == 0:
            print("No files or directories found.")
        else:
            for i, item in enumerate(files):
                prefix = ">> " if i == selected_idx else "   "
                print(f"{prefix}{item}")
        
        # Get key press
        key = getch()
        
        # Handle arrow keys (Windows and Unix)
        if key == '\x1b':  # Escape sequence
            # Check for arrow keys
            key2 = getch()
            if key2 == '[':
                key3 = getch()
                if key3 == 'A' and selected_idx > 0:  # Up arrow
                    selected_idx -= 1
                elif key3 == 'B' and selected_idx < len(files) - 1:  # Down arrow
                    selected_idx += 1
                elif key3 == 'C' and files:  # Right arrow
                    selected = files[selected_idx]
                    if selected.startswith('[D]'):
                        selected_path = os.path.join(current_dir, selected[4:])
                        current_dir = selected_path
                        selected_idx = 0
                elif key3 == 'D':  # Left arrow
                    parent_dir = str(Path(current_dir).parent)
                    if parent_dir != current_dir:  # Prevent going above root
                        current_dir = parent_dir
                        selected_idx = 0
        elif key == 'q':  # Quit
            break
        elif key == '\r':  # Enter key
            if files and 0 <= selected_idx < len(files):
                selected = files[selected_idx]
                selected_name = selected[4:]  # Remove [D] or [F] prefix
                selected_path = os.path.join(current_dir, selected_name)
                
                if selected.startswith('[D]'):
                    current_dir = selected_path
                    selected_idx = 0
                else:
                    if selected_name.endswith('.py'):
                        clear_screen()
                        # Show options for Python files
                        print(f"File: {selected_name}")
                        print("\nOptions:")
                        print("1. Run Python file")
                        print("2. Edit Python file")
                        print("3. Back")
                        
                        while True:
                            option = input("\nChoose an option (1-3): ")
                            if option == '1':
                                clear_screen()
                                run_python_file(selected_path)
                                break
                            elif option == '2':
                                clear_screen()
                                edit_file(selected_path)
                                break
                            elif option == '3':
                                break
                            else:
                                print("Invalid option. Please try again.")
                    elif selected_name.endswith('.sh'):
                        clear_screen()
                        run_shell_script(selected_path)
                    elif selected_name == 'requirements.txt':
                        clear_screen()
                        install_requirements(selected_path)
                    else:
                        print(f"No action defined for {selected_name}")
                        input("\nPress any key to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
