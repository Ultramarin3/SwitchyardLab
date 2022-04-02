#!/usr/bin/env python3

'''
Basic IPv4 router (static routing) in Python.
'''

import sys
import os
import time

from switchyard.lib.packet.util import *
from switchyard.lib.userlib import *
from collections import OrderedDict
from collections import deque
class Router(object):
    def __init__(self, net):
        self.net = net
        self.forwarding_table = self.build_forwarding_table()
        self.arp_table={}        #store ip addr;mapping with timestamp and MAC
        self.queue=OrderedDict()
        self.dyn_Table = deque(maxlen=5)#dynamic_routing_table
        
    def build_forwarding_table(self):
        forwarding_table = []
        lines = [line.rstrip('\n') for line in open('./forwarding_table.txt')]
        for row in lines:
            temp = row.split()
            forwarding_table.append([IPv4Address(temp[0]),IPv4Address(temp[1]),IPv4Address(temp[2]),temp[3]])
        for intf in self.net.interfaces():
            network_prefix = int(intf.ipaddr) & int(intf.netmask)
            temp = [IPv4Address(network_prefix), intf.netmask, None, intf.name] #the network address, the subnet mask, the next hop address, and the interface
            forwarding_table.append(temp)
        return forwarding_table
    
    def check_queue(self):
        for ip in self.queue:
            #Send up to 3 ARP requests for a given IP address. If no ARP reply is received after sending 3 requests, give up and drop the packet and do nothing else.

            if self.queue[ip][2] == 3: 
                del queue[ip]
                continue
            #If no ARP reply is received within 1 second in response to an ARP request, send another ARP request
            if time.time() - self.queue[ip][3] <= 1: 
                intf = self.queue[ip][1]
                self.net.send_packet(intf,create_ip_arp_request(self.net.interface_by_name(intf).ethaddr,self.net.interface_by_name(intf).ipaddr,ip))
                self.queue[ip][3] = time.time() 
                self.queue[ip][2] += 1 #count arp requests
    


    def router_main(self):    
        '''
        Main method for router; we stay in a loop in this method, receiving
        packets until the end of time.
        '''
        my_interfaces = self.net.interfaces()
        my_ip = [intf.ipaddr for intf in my_interfaces]

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
            if gotpkt == False:
                self.check_queue()
            else:
                log_debug("Got a packet: {}".format(str(pkt)))
                arp = pkt.get_header(Arp)
                ipv4_h = pkt.get_header(IPv4)
                dyn_h = pkt.get_header_by_name("DynamicRoutingMessage")
                reply_handled = False
                if arp:
                    #handle Arp request, make an Arp reply
                    if arp.operation==ArpOperation.Request:
                        for intf in my_interfaces:
                            if arp.targetprotoaddr == intf.ipaddr:
                                self.net.send_packet(intf,create_ip_arp_reply(intf.ethaddr,arp.senderhwaddr,arp.targetprotoaddr,arp.senderprotoaddr))
                    #handle arp reply
                    elif arp.operation==ArpOperation.Reply:
                        for intf in my_interfaces:
                            if arp.targetprotoaddr in my_ip:
                                self.arp_table[arp.senderprotoaddr] = [arp.senderhwaddr,time.time()] #record a IP-MAC mapping with timestamp
                        if arp.senderprotoaddr in self.queue:#if the ip is already recorded
                            out_intf = self.queue[arp.senderprotoaddr][1]
                            #complete eth header for each packet buffered by this ip and send  out
                            for packet in self.queue[arp.senderprotoaddr][0]:
                                if not packet[0]:
                                    packet+=Ethernet()
                                packet[0].src = self.net.interface_by_name(out_intf).ethaddr
                                packet[0].dst = arp.senderhwaddr
                                self.net.send_packet(out_intf,packet)
                            del self.queue[arp.senderprotoaddr]
                            reply_handled = True
                self.check_queue()
                if reply_handled == True:
                    continue
                if ipv4_h:
                    ipv4_h.ttl-=1#Decrement the TTL field in the IP header by 1, check if the packet have no ttl left or destinate to my_ip
                    if ipv4_h.ttl < 0:
                        continue
                    if ipv4_h.dst in my_ip:
                        continue
                    #lpm
                    #first dynammic routing table and then forwarding table
                    max = -1
                    match = None
                    for entry in list(self.dyn_Table):
                        netaddr = IPv4Network(str(entry[0])+'/'+str(entry[1]))
                        if ipv4_h.dst in netaddr:
                            if netaddr.prefixlen > max:
                                max = netaddr.prefixlen
                                match = entry
                    if match==null:
                        for entry in self.forwarding_table:
                            netaddr = IPv4Network(str(entry[0])+'/'+str(entry[1]))
                            if ipv4_h.dst in netaddr:
                                if netaddr.prefixlen > max:
                                    max = netaddr.prefixlen
                                    match = entry
                    if not match:#no match, drop packet
                        continue
                    next_hop = match[2] if match[2] else ipv4_h.dst#when it is none use destIP of incomming packet itself
                    intf_name = match[3]
                    if next_hop in self.arp_table:#already have destMAC because of previous request - simple lookup & add eth header & send
                        if not pkt[0]:
                            pkt+=Ethernet()
                        pkt[0].src = self.net.interface_by_name(intf_name).ethaddr
                        pkt[0].dst = self.arp_table[next_hop][0]
                        self.net.send_packet(intf_name,pkt)
                        self.arp_table[next_hop][1] = time.time() #update time of use this arp entry
                    else:#do not havehandling ARP queries ,handling ARP queries 
                        if next_hop in self.queue:#already have this ip entry in the queue
                            self.queue[next_hop][0].append(pkt)
                        else:#send request and add the entry to queue
                            self.net.send_packet(intf_name,create_ip_arp_request(self.net.interface_by_name(intf_name).ethaddr,self.net.interface_by_name(intf_name).ipaddr,next_hop))
                            self.queue[next_hop] = [[pkt], intf_name, 1, time.time()]
                if dyn_h:
                    new_dyn = [dyn_h.advertised_prefix, dyn_h.advertised_mask, dyn_h.next_hop, dev]
                    self.dyn_Table.append(new_dyn)
def main(net):
    '''
    Main entry point for router.  Just create Router
    object and get it going.
    '''
    r = Router(net)
    r.router_main()
    net.shutdown()
