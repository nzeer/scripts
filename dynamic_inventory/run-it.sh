#!/bin/bash

# scan subnet(s)
# each subnet needs its own nmap plugin, name doesnt matter, stored inside ./nmap
# writes out data to ./json_hosts_data 
#python scan.py

# converts everything from each subnet stored in json_hosts_data to ./inventory for use with gather_facts
# preps directory structure for gather_facts
#python json2yaml.py

# loads facts for every host in inventory, writes out each host to its own file inside ./hosts and out/hosts.csv
#ansible-playbook -i inventory gather_facts.yml

# parses files in ./hosts
# writes inventory/world/child data inside ./inventories
# copies anything in ./static to ./inventories
#python parse.py
dirname=/home/rjackson/dynamic_inventory_live/
cd "$(dirname "$0")";
CWD="$(pwd)"
echo $CWD


python ./scan.py && python ./json2yaml.py && ansible-playbook -i ./inventory ./gather_facts.yml;
python ./parse.py
