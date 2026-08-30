"""=======================================================================

Author: Rob Jackson

Parses hosts.csv 
for future use.

=========================================================================="""
import csv

HOSTS_CSV = "./csv/hosts.csv"

with open(HOSTS_CSV, newline="") as csvfile:
    spamreader = csv.reader(csvfile, delimiter=";", quotechar="|")
    for row in spamreader:
        print(", ".join(row))
