import subprocess, sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
# HiddenCloud installs to .local/ but /usr/local/bin/python doesn't look there
local_site = os.path.join(os.getcwd(), '.local', 'lib', f'python{sys.version_info.major}.{sys.version_info.minor}', 'site-packages') #SN
env = os.environ.copy()
if os.path.isdir(local_site):
    env['PYTHONPATH'] = local_site + os.pathsep + env.get('PYTHONPATH', '')
subprocess.run([sys.executable, '-m', 'bot'], check=True, env=env)
