#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess



cmd='echo'+"from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin')"+' | /usr/bin/python3   /usr/bin/numeriseur/webservice/config_web/manage.py shell'
os.system('/usr/bin/python3  /usr/bin/numeriseur/webservice/config_web/manage.py migrate')
os.system(cmd)

server_run=False

while True:
    usb_connected=subprocess.getoutput('cat /sys/class/udc/49000000.usb-otg/state')
    if usb_connected=='configured' and not server_run:

    	
        os.system('/usr/bin/python3  /usr/bin/numeriseur/webservice/config_web/manage.py runserver 0.0.0.0:8000')
        
        server_run=True
        os.system('systemctl stop numeriseur-load.service')
        os.system('systemctl stop microphone-load.service')
    else :
        os.system('pkill -f runserver')
        server_run=False
        

    



    




