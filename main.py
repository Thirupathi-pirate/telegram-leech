import subprocess, sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--quiet"], check=True)
subprocess.run([sys.executable, "-m", "bot"], check=True) #RR
