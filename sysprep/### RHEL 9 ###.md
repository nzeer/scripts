### RHEL 9 ###
 
#> Setup Interface (YOUR) WS
- vim ifcfg-ens224
- nmcli con show
- nmcli con down ens224
- nmcli con up ens224
- ip a
- nmcli con load /etc/sysconfig/network-scripts/ifcfg-ens224
 
#> Cloning
- power down stig image
- clone to virtual machine
- Never put on 131.45.83.129 (host)
- Put on .155 (host)
- disable SA [ ] (Connect) Network Adapter ON MIGRATING HOST
 
#> New Host
- take down network
- change Network adapter (Build new Network Interfaces - leave Interfaces down! - Disable connect at PowerOn)
- start network (reboot if issue w/ Network)
- hostnamectl set-hostname (NEW HOSTNAME)
- edit /etc/humanhostname
- Reboot for new hostname

# edit splunk
- edit splunk forwarder
> /opt/splunkforwarder/etc/system/local/inputs.conf (change hostname)
> /opt/splunkforwarder/etc/system/local/server.conf (change hostname)
 
#> Lift and Shift Software
- firewall-cmd --permanent --add-port=$PORT/tcp
- firewall-cmd --permanent --add-port=$PORT/udp
- firewall-cmd --reload
- firewall-cmd --list-all
- for i in `find /var/log -type d`; do setfacl -m u:splunk:rx $i; done
- splunk list add monitor $DIR_TO_MON
 
#> Check CPU and Memory on VM to match ORIG Server
 
#> Enable new host
- schedule downtime nagios for host
- set nic on new host with LIVE ip
- disable nic on existing host
- swap 10.1.10.x to old host
 
#> Post setup
- copy /etc/host from old host to new host
- add splunk monitor at boot
> /opt/splunkforwarder/bin/splunk enable boot-stop ( OLD HOST )
> /opt/splunkforwarder/bin/splunk enable boot-start ( NEW HOST )
- setup rsyslog
> vim /etc/rsyslog.conf
>> # add at the bottom:
>> *.* @10.1.1.225
> systemctl restart rsyslog.service
- setup cronjobs
- /usr/local/scripts/avdat-sheck.sh
> run
- /usr/local/scripts/passwdcheck.sh 
> /usr/local/scripts/logs (Remove old entry)
> Server Name Array
>> PrivServerIP (CHANGE)
> manually run passwdcheck.sh
 
- enable nagios (Contact John - Email)
> systemctl enable ncpa.service
> systemctl start ncpa.service
- update ansible host
 
#> Send Rob Email about Host/IP to migrate ansible inventory
> and everyone so everyone knows to update their ssh known_hosts / ansible inv