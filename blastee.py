import sys
from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.userlib import *

ENDIAN='big'



def switchy_main(net):
    intf = net.interface_by_name('blastee-eth0')
    blaster_ip = IPv4Address("192.168.100.1")
    target_ethaddr = EthAddr('40:00:00:00:00:02') # see start_mininet.py
    payload = b'\xff' * 8
    while True:
        try:
            _, _, packet = net.recv_packet()
            contents = packet.get_header(RawPacketContents)
            if contents == None:
                log_debug('Ignored packet of unknown type')
                return
            seq_num = int.from_bytes(contents.data[:4], 'big')
            log_info("Got packet seq_num = {}".format(seq_num))

            etp = Ethernet(
                src = intf.ethaddr,
                dst = target_ethaddr
            )
            ip = IPv4(
                protocol = IPProtocol.UDP,
                src = intf.ipaddr,
                dst = blaster_ip,
                ttl = 64
            )
            pkt = etp + ip + UDP() + seq_num.to_bytes(4, ENDIAN) + payload
            try:
                net.send_packet(intf.name, pkt)
            except ValueError as e:
                log_debug("Failed to send packet due to ValueError: {}".format(str(e)))
            except:
                log_debug("Failed to send packet due to unknown error: {}".format(sys.exc_info()[0]))
            
            
        except NoPackets:
            log_debug("No packets available in recv_packet")
            continue
        except Shutdown:
            log_debug("Got shutdown signal")
            break
    net.shutdown()