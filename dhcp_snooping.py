import dpkt
import ipaddress
import nflog
import select
import time

import backend
import db

class DHCPSnooping:
    def __init__(self, backend, db, nflog_group):
        self.backend = backend
        self.db = db
        self.nflog_group = nflog_group

    def setup(self):
        self.backend.setup()
        self.db.setup()
        for client_mac, client_ip, timestamp, lease_time in self.db.leases():
            self.backend.allow_dhcp_binding(client_mac, client_ip)
        nflog.setgroup(self.nflog_group) 
        nflog.setcb(self.process_dhcp_packet)

    def run(self):
        nflog.start()
        fd = nflog.getfd()
        poll_handle = select.poll()
        poll_handle.register(fd, select.POLLIN)
        while True:
            plist = poll_handle.poll(5000)
            if len(plist) > 0:
                nflog.handle()

    def process_dhcp_packet(self, indev, ifname, proto,
                            payload_len, payload,
                            hwll_hdr_len, hwll_hdr):
        ip_packet = dpkt.ip.IP(payload)
        udp_packet = ip_packet.data
        dhcp_packet = dpkt.dhcp.DHCP(udp_packet.data)
        # only handle DHCP replies
        print(dhcp_packet.op)
        if dhcp_packet.op != 2:
            return
        options = {opt: val for opt, val in dhcp_packet.opts}
        # only handle DHCP ACKs
        print(options[53])
        # -> not a good idea, sometimes there is an offer but no additional req+ack
        #if options[53] != 5:
        #    return
        print(dhcp_packet.yiaddr)
        client_mac = ":".join(hex(i)[2:].zfill(2) for i in dhcp_packet.chaddr)
        client_ip = ipaddress.ip_address(dhcp_packet.yiaddr)
        print(client_mac, client_ip)
        if 51 not in options:
            print("No lease time!")
            return
        lease_time = int(sum([d * 256 ** i for i, d in enumerate(reversed(options[51]))]))
        if not self.db.has_lease(client_mac, client_ip):
            self.backend.allow_dhcp_binding(client_mac, client_ip)
        self.db.store_lease(client_mac, client_ip, lease_time)
        # cleanup, maybe checked too often
        current_time = time.time()
        self.db.filter_leases(
            lambda c_mac, c_ip, ts, lt: ts + lt >= current_time,
            lambda c_mac, c_ip, ts, lt: self.backend.withdraw_dhcp_binding(c_mac, c_ip)
        )
        print('\n')


if __name__ == "__main__":
    backend = backend.IPTablesBackend(dry_run=True)
    db = db.CSVDatabase("leases.csv")
    app = DHCPSnooping(backend, db, 1)
    app.setup()
    app.run()
