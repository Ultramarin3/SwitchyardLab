# Overview
Part1: 
Implement the core functionalities of an Ethernet learning switch using the Switch framework. When Ethernet frames arrive on any port, the switch process the header of the frame to obtain information about the destination host. If the switch knows that the host is reachable through one of its ports, it sends out the frame from the appropriate output port. If it does not know where the host is, it floods the frame out of all ports except the input port.LRU mechanism is used to update the forwarding table.
Part2:
Implemet a functional IPv4 router. The router has the following capabilities:1.Responding to/Making ARP requests. 2.Receiving packets and forwarding them to their destination by using a lookup table. 
Part3:
build a reliable communication library in Switchyard that will consist of 3 agents. At a high level, a blaster will send data packets to a blastee through a middlebox. IP only offers a best-effort service of delivering packets between hosts. This means all sorts of bad things can happen to packets once they are in the network: they can get lost, arbitrarily delayed or duplicated. The communication library will provide additional delivery guarantees by implementing sliding window mechanisms at the blaster and blastee. 
