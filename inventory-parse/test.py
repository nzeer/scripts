import ipaddress

def ip_in_range(ip, ranges):
    print("testing ip: ",ip)
    for range in ranges:
        print("testing range: ",range)
        if ipaddress.ip_address(ip) in ipaddress.ip_network(range):
            print(ip + " is in range " + range)
            return True
    return False

def parse_ansible_hosts(file_path):
    hosts = []
    valid_ranges = ["10.1.1.0/24", "192.168.131.0/24", "137.244.161.0/24", "137.244.170.0/24"]
    skip_section = False
    with open(file_path, 'r') as file:
        for line in file:
            print(line)
            line = line.strip()
            if line.startswith("["):
                # Check if the section is [unknown], if so, skip it
                skip_section = "unknown" in line.lower()
                continue
            if skip_section or not line or line.startswith("#"):
                continue
            if ip_in_range(line, valid_ranges):
                hosts.append(line)
    return hosts

print(parse_ansible_hosts('./inventory'))

# The rest of the script remains largely the same
