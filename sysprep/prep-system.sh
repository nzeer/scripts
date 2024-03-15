# 209.160.33.152
echo "Disabling firewalld and fapolicyd."
systemctl stop firewalld
systemctl disable firewalld

systemctl stop fapolicyd
systemctl disable fapolicyd

echo "Disabling SELinux."
setenforce 0

python3 ./prep-hostname.py && echo "Hostname configured."
python3 ./prep-network. && echo "Network configured."
python3 ./prep-splunk.py && echo "Splunk configured."
python3 ./prep-rsyslog.py && echo "Rsyslog configured."
python3 ./prep-hosts.py && echo "Hosts configured."
echo "System prepped."