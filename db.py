import ipaddress
import time

class CSVDatabase:
    def __init__(self, leasefile):
        self.leasefile = leasefile
        self.dhcp_leases = {}

    def setup(self):
        with open(self.leasefile, "r") as f:
            for lease in f:
                client_mac, client_ip, timestamp, lease_time = lease.split(",")
                client_ip = ipaddress.ip_address(client_ip)
                self.dhcp_leases[(client_mac, client_ip)] = (float(timestamp), int(lease_time))

    def leases(self):
        for (client_mac, client_ip), (timestamp, lease_time) in self.dhcp_leases.items():
            yield client_mac, client_ip, timestamp, lease_time

    def has_lease(self, client_mac, client_ip):
        return (client_mac, client_ip) in self.dhcp_leases

    def store_lease(self, client_mac, client_ip, lease_time):
        self.dhcp_leases[(client_mac, client_ip)] = (time.time(), lease_time)
        self.__write_to_file()

    def filter_leases(self, f, cb):
        filtered_dhcp_leases = {}
        for (client_mac, client_ip), (timestamp, lease_time) in self.dhcp_leases.items():
            if f(client_mac, client_ip, timestamp, lease_time):
                filtered_dhcp_leases[(client_mac, client_ip)] = (timestamp, lease_time)
            else:
                cb(client_mac, client_ip, timestamp, lease_time)
        self.dhcp_leases = filtered_dhcp_leases
        self.__write_to_file()

    def __write_to_file(self):
        with open(self.leasefile, "w") as f:
            for (client_mac, client_ip), (timestamp, lease_time) in self.dhcp_leases.items():
                f.write("{mac},{ip},{timestamp},{lease_time}\n".format(
                    mac=client_mac,
                    ip=client_ip,
                    timestamp=timestamp,
                    lease_time=lease_time
                ))
