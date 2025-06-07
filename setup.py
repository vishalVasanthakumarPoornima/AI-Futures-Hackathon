import subprocess
import shutil
import sys
import os
import importlib.util
import platform

FRONTEND_DIR = "AI-futures-hackathon"
NORMAL_DIR = ""


REQUIRED_PYTHON_PACKAGES = [
    "fastapi",
    "uvicorn",
    "requests"
]

def install_python_dependencies():
    for package in REQUIRED_PYTHON_PACKAGES:
        if importlib.util.find_spec(package) is None:
            print(f"Installing missing Python package: {package}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def check_installed(command):
    return shutil.which(command) is not None

def is_python_module_installed(module_name):
    return importlib.util.find_spec(module_name) is not None

def open_new_terminal(commands, title=""):
    system = platform.system()

    if system == "Windows":
        test_cmd = ' && '.join(commands)
        cmd = f'start "{title}" cmd /k "{test_cmd}"'
        subprocess.Popen(cmd, shell=True)

    elif system == "Darwin":  # macOS
        script = '; '.join(commands)
        osa_cmd = f'''
        tell application "Terminal"
            do script "{script}"
            activate
        end tell
        '''
        subprocess.run(["osascript", "-e", osa_cmd])

    else:
        print(f"⚠️ Unsupported platform: {system}")

def main():
    print("Checking dependencies...")

    missing = []

    for cmd in ["node", "npm", "ollama"]:
        if not check_installed(cmd):
            missing.append(cmd)

    install_python_dependencies()

    if missing:
        print(f" Missing: {', '.join(missing)}")
        print(" Please install the above before continuing.")
        return

    # Commands to run
    print("Launching services...")

    # Start Ollama and pull Mistral
    open_new_terminal([
        "ollama pull mistral"
    ], title="Ollama")

    # Start Uvicorn API backend
    open_new_terminal([
        f"cd {NORMAL_DIR}",
        "uvicorn main:app --reload"
    ], title="Uvicorn")

    # Start Frontend
    frontend_path = os.path.abspath(FRONTEND_DIR)
    open_new_terminal([
        f"cd {frontend_path}",
        "npm install",
        "npm run dev"
    ], title="Frontend")

if __name__ == "__main__":
    main()

