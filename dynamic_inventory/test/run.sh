# scan network
ansible-inventory -i nmap.yaml --export --output=hosts.json --list

# convert hosts.json to inventory file
python json2ini2.py

ansible-playbook -i inventory gather_facts.yml

