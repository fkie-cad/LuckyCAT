#!/bin/bash
IP=$(ip route get 1 | awk '{print $NF;exit}')
echo "Current ip address is $IP"

echo "Installing Lucky CAT"
cd /opt/luckycat || exit
ln -s /opt/luckycat/luckycat/frontend/nginx.conf /etc/nginx/sites-enabled
service nginx restart
python3 /opt/luckycat/setup.py install &>/dev/null

echo "Starting Lucky CAT frontend"
uwsgi --ini /opt/luckycat/luckycat/frontend/uwsgi.ini
