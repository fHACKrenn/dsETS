from jupyter_server.auth import passwd
import os
p=os.getenv('PASSWORD') or 'sembarang1234'
print(passwd(p,'sha1'))
