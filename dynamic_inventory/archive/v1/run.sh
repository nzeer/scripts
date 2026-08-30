# scan network
mkdir hosts
ansible-inventory -i nmap.yaml --export --output=hosts.json --list

# convert hosts.json to inventory file
python json2yaml.py

# loads facts for every host in inventory, writes out each host to its own file inside ./hosts
ansible-playbook -i inventory gather_facts.yml

# parses files in ./hosts and writes out inventory inside ./inventories
python parse.py
