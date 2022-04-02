import sys
import collections
import pdb
from switchyard.lib.userlib import *

def isBroadcast(src):
    return SpecialEthAddr.ETHER_BROADCAST.value == src

class ForwardingTable(collections.OrderedDict):
    def __init__(self, size=5):
        self.size = size
        self.cache = collections.OrderedDict()
        return

    def __iter__(self):
        return iter(self.cache)

    def __getitem__(self, item):
        return self.cache[item]

    def update(self, src, dst, port):

        # If broadcast addr,do nothing.
        if isBroadcast(src):
            return
            
        #If the addr is already recorded,update it as the most recent used.
        if src in self.cache:
            self.cache.pop(src)
            self.cache[src] = port
        #If addr not in map, we update ForwardingTable in a lru manner
        else:
            if len(self.cache) == self.size:
                self.cache.popitem( last = False)  
                self.cache[src] = port  
            else:    
                self.cache[src] = port
                
        #If the addr is already recorded,update it as the most recent used.
        if dst in self.cache:
             val = self.cache.pop(dst)
             self.cache[dst] = val
             return
        
        return




def broadcast(net, e, block, pkt):
    for intf in e:
        if intf.name != block:
            net.send_packet(intf.name, pkt)


def main(net):
    my_interfaces = net.interfaces()
    mymacs = [intf.ethaddr for intf in my_interfaces]
    forwarding_table = ForwardingTable()
    
    while True:
        try:
            _, input_port, packet = net.recv_packet()
        except NoPackets:
            continue
        except Shutdown:
            return

        forwarding_table.update(packet[0].src, packet[0].dst, input_port)

        log_debug("In {} received packet {} on {}".format(
            net.name, packet, input_port))

        if packet[0].dst in mymacs:
            log_debug("Packet intended for me")
            continue

        #if packet[0].dst in forwarding_table:
        if forwarding_table.cache.__contains__(packet[0].dst):
            net.send_packet(forwarding_table[packet[0].dst], packet)
            continue
        broadcast(net, my_interfaces, input_port, packet)

    net.shutdown()
