#!/usr/bin/env python3

'''
Basic IPv4 router (static routing) in Python.
'''

import sys
import os
import time

from switchyard.lib.packet.util import *
from switchyard.lib.userlib import *

class Router(object):
    def __init__(self, net):
        self.net = net
        # other initialization stuff here


    def router_main(self):    

        while True:
            gotpkt = True
            try:
                timestamp,dev,pkt = self.net.recv_packet(timeout=1.0)
            except NoPackets:
                log_debug("No packets available in recv_packet")
                gotpkt = False
            except Shutdown:
                log_debug("Got shutdown signal")
                break

            if gotpkt:
                log_debug("Got a packet: {}".format(str(pkt)))
                arp_table={}
                arp = pkt.get_header(Arp)
                if arp:
                    my_interfaces = self.net.interfaces()
                    if arp.operation==ArpOperation.Request:
                        for intf in my_interfaces:
                            if arp.targetprotoaddr == intf.ipaddr:
                                reply_pkt = create_ip_arp_reply(intf.ethaddr,arp.senderhwaddr,arp.targetprotoaddr,arp.senderprotoaddr)
                                self.net.send_packet(intf,reply_pkt)
                    elif arp.operation==ArpOperation.Reply:
                        for intf in my_interfaces:
                            if arp.targetprotoaddr == intf.ipaddr:
                                arp_table[arp.senderprotoaddr] = arp.senderhwaddr 
def main(net):
    '''
    Main entry point for router.  Just create Router
    object and get it going.
    '''
    r = Router(net)
    r.router_main()
    net.shutdown()
