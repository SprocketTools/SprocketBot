# launcher.py

import subprocess
import sys
import os
import time
import glob
import signal
import platform
import tempfile

# This dictionary will be shared between the main loop and the shutdown handler
managed_processes = {}

def is_process_running(pid: int) -> bool:
    """A cross-platform check to see if a process with a given PID is running."""
    if platform.system() == "Windows":
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            return str(pid) in result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    else:
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True

def launch_celestial_navigator():
    # ... (This function is unchanged)
    pidfile = os.path.join(tempfile.gettempdir(), "celestial_navigator.pid")
    python_executable = sys.executable
    command = [python_executable, 'celestial_navigator.py']
    if os.path.isfile(pidfile):
        try:
            with open(pidfile, 'r') as f: pid = int(f.read())
            if is_process_running(pid):
                print(f"--- Celestial Navigator is already running (PID: {pid}). ---")
                return
            else:
                print("--- Found stale PID file. Removing and starting navigator. ---")
                os.remove(pidfile)
        except (ValueError, FileNotFoundError): pass
    print("--- Launching Celestial Navigator process... ---")
    creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0
    subprocess.Popen(command, creationflags=creation_flags)
    time.sleep(2)

def run_update_and_pull():
    # ... (This function is unchanged)
    if platform.system() != "Windows":
        print("--- Checking for updates from GitHub... ---")
        try:
            print("Stashing local changes (if any)...")
            subprocess.run(["git", "stash"], capture_output=True, text=True)
            print("Pulling latest code...")
            subprocess.run(["git", "pull"], check=True, capture_output=True, text=True)
            print("--- Code is up to date. ---")
            return True
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            print(f"--- ERROR: Git command failed. --- {e}")
            return False
    else:
        print("--- Skipping Git update check on Windows. ---")
        return True

def main_process_manager():
    """The main process manager loop that populates the managed_processes dict and monitors them."""
    config_dir = "C:\\SprocketBot\\bots\\" if platform.system() == "Windows" else os.path.join(os.path.expanduser("~"), "bots")
    config_files = glob.glob(os.path.join(config_dir, "*.ini"))

    if not config_files:
        print(f"No configuration files found in '{config_dir}'. Exiting.")
        return

    python_executable = sys.executable

    for config_file in config_files:
        config_name = os.path.basename(config_file).replace('.ini', '')
        command = [python_executable, 'main.py', config_name]
        print(f"Starting instance '{config_name}'...")
        creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0
        managed_processes[config_name] = subprocess.Popen(command, creationflags=creation_flags)
        time.sleep(3)

    print(f"--- Launched {len(managed_processes)} bot instances. Monitoring... ---")

    while True:
        restart_needed = False
        for instance_name, process in managed_processes.items():
            if process.poll() is not None:
                print(f"\n--- Instance '{instance_name}' has stopped (Exit Code: {process.poll()}). ---")
                print("--- Triggering a full system update and restart. ---")
                restart_needed = True
                break

        if restart_needed:
            # This loop now just stops processes before a restart cycle
            for other_name, other_proc in managed_processes.items():
                if other_proc.poll() is None:
                    print(f"Stopping instance '{other_name}' (PID: {other_proc.pid})...")
                    if platform.system() == "Windows":
                        os.kill(other_proc.pid, signal.CTRL_C_EVENT)
                    else:
                        other_proc.terminate()
            for proc in managed_processes.values():
                proc.wait()
            # Clear the dictionary for the new cycle
            managed_processes.clear()
            return
        time.sleep(10)

if __name__ == "__main__":
    try:
        launch_celestial_navigator()
        while True:
            if not run_update_and_pull():
                print("--- Halting due to update failure. Please fix manually. ---")
                break
            main_process_manager()
            print("--- Restarting all bot services in 5 seconds... ---")
            time.sleep(5)
    finally:
        # This 'finally' block will run on Ctrl+C or any other exit.
        print("\nLauncher shutting down. Stopping all managed processes...")

        # Stop the main bot processes
        for name, proc in managed_processes.items():
            if proc.poll() is None:
                print(f"Stopping instance '{name}' (PID: {proc.pid})...")
                if platform.system() == "Windows":
                    os.kill(proc.pid, signal.CTRL_C_EVENT)
                else:
                    proc.terminate()

        # Stop the independent music player
        pidfile = os.path.join(tempfile.gettempdir(), "celestial_navigator.pid")
        if os.path.isfile(pidfile):
            try:
                with open(pidfile, 'r') as f:
                    pid = int(f.read())
                if is_process_running(pid):
                    print(f"--- Sending shutdown signal to Celestial Navigator (PID: {pid}). ---")
                    if platform.system() == "Windows":
                        os.kill(pid, signal.CTRL_C_EVENT)
                    else:
                        os.kill(pid, signal.SIGTERM)
            except (OSError, ValueError):
                pass