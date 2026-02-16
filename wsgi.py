# WSGI entry for PythonAnywhere (and other WSGI servers).
# On PythonAnywhere: set "Source code" path to this project folder, then in the
# WSGI config file use the path below (replace YOUR_USERNAME with your PA username).

import sys

# Path to the project folder (PythonAnywhere: /home/YOUR_USERNAME/vietnam-stock-telegram)
path = "/home/YOUR_USERNAME/vietnam-stock-telegram"
if path not in sys.path:
    sys.path.insert(0, path)

from app import app as application
