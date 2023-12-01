# scan network
cd /home/nzeer/repos/semaphore-repo/gather_facts
ansible-inventory -i nmap.yaml --export --output=hosts.json --list

# copy hosts.json to dynamic inventory
cp hosts.json /home/nzeer/repos/scripts/dynamic_inventory

# convert hosts.json to inventory file
cd /home/nzeer/repos/scripts/dynamic_inventory
python json2ini2.py

# collect os information
ansible all -m setup -a 'filter=ansible_distribution*' -i inventory > os-data.json


