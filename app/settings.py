import os

MONGO_URI = os.getenv('MONGO_URI')
SECRET_KEY = os.getenv('SECRET_KEY')
LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
SENDMAIL = os.environ.get('SENDMAIL', 'FALSE').upper()
DOMAIN = os.environ.get('DOMAIN', '.leafarlins.com')
if SENDMAIL == "TRUE":
    SENDMAIL = True
else:
    SENDMAIL = False
