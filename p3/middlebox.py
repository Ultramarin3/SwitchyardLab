from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.packet.util import *
from switchyard.lib.userlib import *
import random
import time
import sys

def drop(percent):
    return random.randrange(100) < percent

def delay(mean, std):
    delay =random.gauss(mean, std)
    print(delay)
    if delay > 0:
        time.sleep(delay/1000)



#update_pkt
def update_pkt(pkt, out_port, out_dst):
    del pkt[0]
    eth_head = Ethernet(src=out_port, dst=out_dst, ethertype=EtherType.IPv4)
    pkt.prepend_header(eth_head)
    pkt[IPv4].ttl -= 1




def switchy_main(net):

    my_intf = net.interfaces()
    mymacs = [intf.ethaddr for intf in my_intf]
    myips = [intf.ipaddr for intf in my_intf]
    contents = open('./middlebox_params.txt',"r")
    for line in contents.readlines():
        value = line.split()
        s = int(value[1])    #random seed
        prob = int(value[3]) #probability of drop packet
        dm = int(value[5])   #mean delay time
        dstd = int(value[7]) #mean standard deviation

    random.seed(s) #Extract random seed from params file

    while True:
        gotpkt = True
        try:
            _,dev,pkt = net.recv_packet()
            log_debug("Device is {}".format(dev))
        except NoPackets:
            log_debug("No packets available in recv_packet")
            gotpkt = False
        except Shutdown:
            log_debug("Got shutdown signal")
            break
        
        if gotpkt:
            log_debug("I got a packet {}".format(pkt))
            if dev == "middlebox-eth1":
                log_debug("Received from blastee")

                out_intf = net.interface_by_name("middlebox-eth0")
                update_pkt(pkt, out_intf.ethaddr, '10:00:00:00:00:01')
                log_debug("Sending packet: {}".format(pkt))
                net.send_packet("middlebox-eth0", pkt)

            elif dev == "middlebox-eth0":
                log_debug("Received from blaster")

                if drop(prob):
                    log_debug("Dropping packet")
                else:
                    delay(dm, dstd)
                    out_intf = net.interface_by_name("middlebox-eth1")
                    update_pkt(pkt, out_intf.ethaddr, '20:00:00:00:00:01')
                    log_debug("Sending packet: {}".format(pkt))
                    net.send_packet("middlebox-eth1", pkt)
            
            else:
                log_debug("Oops :))")

    net.shutdown()
