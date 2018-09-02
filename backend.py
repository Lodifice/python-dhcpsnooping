import os

class IPTablesBackend:
    IPTABLES_CMD = ("iptables -{op} dhcp_snooping -s {client_ip} "
                    "-m mac --mac-source {client_mac} -j ACCEPT\n"
                    "iptables -{op} dhcp_snooping -d {client_ip} -j ACCEPT")

    def __init__(self, nflog_debug_group=2, dry_run=False):
        self.nflog_debug_group = nflog_debug_group
        self.dry_run = dry_run

    def setup(self):
        os.system("iptables -F dhcp_snooping")
        os.system(
            "iptables -A dhcp_snooping -j NFLOG --nflog-group {}".format(
                self.nflog_debug_group
            )
        )
        if not self.dry_run:
            os.system("iptables -A dhcp_snooping -j DROP")

    def allow_dhcp_binding(self, client_mac, client_ip):
        self.__run_iptables_cmd("I", client_ip, client_mac)

    def withdraw_dhcp_binding(self, client_mac, client_ip):
        self.__run_iptables_cmd("D", client_ip, client_mac)

    def __run_iptables_cmd(self, op, client_ip, client_mac):
        cmd = self.IPTABLES_CMD.format(
            op=op,
            client_ip=client_ip,
            client_mac=client_mac
        )
        print(cmd)
        os.system(cmd)
