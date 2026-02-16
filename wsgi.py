# This file contains the WSGI configuration required to serve up your
# web application at http://<your-username>.pythonanywhere.com/
# It works by setting the variable 'application' to a WSGI handler of some
# description.
#
# The below has been auto-generated for your Flask project
import os
os.environ["TELEGRAM_BOT_TOKEN"] = "8343689916:AAHkGGhlfDEaaxIcT29pBgTez6y_OPIKeYM"
os.environ["TELEGRAM_CHAT_ID"] = "8211167936"
os.environ["VNSTOCK_API_KEY"] = "vnstock_681c395729d64852d7f7cad100a905cf"
os.environ["DATABASE_URL"] = "postgresql://postgres:XBzj%25ZPLFDynr9H@db.qmhlpfixzcqnripmyjsh.supabase.co:5432/postgres"

import sys

# add your project directory to the sys.path
project_home = '/home/136leonard/vietnam-stock-telegram'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# import flask app but need to call it "application" for WSGI to work
from app import app as application  # noqa
