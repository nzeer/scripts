# 209.160.33.152

systemctl stop firewalld
systemctl disable firewalld
systemctl stop fapolicyd
systemctl disable fapolicyd
setenforce 0

python3 ./prep-hostname.py
python3 ./prep-network.py
python3 ./prep-splunk.py
python3 ./prep-rsyslog.py