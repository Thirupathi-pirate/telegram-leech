import subprocess, sys, os, shutil
os.chdir(os.path.dirname(os.path.abspath(__file__)))
# HiddenCloud creates .env but bot reads config.env
if not os.path.isfile('config.env') and os.path.isfile('.env'):
    shutil.copy('.env', 'config.env')
# HiddenCloud installs to ~/.local/lib/pythonX.Y/site-packages
pyver = f'python{sys.version_info.major}.{sys.version_info.minor}'
local_site = os.path.expanduser(f'~/.local/lib/{pyver}/site-packages')
if not os.path.isdir(local_site):
    local_site = os.path.join(os.getcwd(), '.local', 'lib', pyver, 'site-packages')
env = os.environ.copy()
if os.path.isdir(local_site):
    env['PYTHONPATH'] = local_site + os.pathsep + env.get('PYTHONPATH', '')
# Ensure pkg_resources is importable from the local site-packages
subprocess.run([sys.executable, '-m', 'pip', 'install', '--target', local_site, 'setuptools<71'], check=False, env=env)
subprocess.run([sys.executable, '-m', 'bot'], check=True, env=env)
