echo "========================"
echo "Beginning sysprep"
echo "========================"

echo "Disabling SELinux."
setenforce 0

python3 ./prep-preinstall.py && echo "Preinstall complete."
python3 ./prep-hostname.py && echo "Hostname configured."
python3 ./prep-network.py && echo "Network configured."
python3 ./prep-splunk.py && echo "Splunk configured."
python3 ./prep-rsyslog.py && echo "Rsyslog configured."
python3 ./prep-hosts.py && echo "Hosts configured."
pyhton3 ./prep-yum-clean-update.py && echo "Yum updated."
echo "System prepped."