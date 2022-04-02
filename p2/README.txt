
Now that you have built a simple learning Ethernet switch and feel more comfortable with the Switchyard framework, you will get to do even more cool stuff using it. In this assignment, you are going to complete a series of tasks to eventually create a fully functional IPv4 router. At a high level, your router will have the following capabilities:

Responding to/Making ARP requests
Receiving packets and forwarding them to their destination by using a lookup table
Responding to/Generating ICMP messages
Details

In order to create this cool router with the aforementioned capabilities, you will implement 5 main functionalities:

Respond to ARP (Address Resolution Protocol) requests for addresses that are assigned to interfaces on the router
Make ARP requests for IP addresses that have no known Ethernet MAC address. A router will often have to send packets to other hosts, and needs Ethernet MAC addresses to do so
Receive and forward packets that arrive on links and are destined to other hosts. Part of the forwarding process is to perform address lookups ("longest prefix match" lookups) in the forwarding information base. You will eventually just use "static" routing in your router, rather than implement a dynamic routing protocol like RIP or OSPF

You can find more detailed information on these functionalities on the following web pages:
Item #1 (https://github.com/jsommers/switchyard/blob/master/examples/exercises/router/router1.rst
Item #2 and Item #3 https://github.com/jsommers/switchyard/blob/master/examples/exercises/router/router2.rst
Address Resolution Protocol (ARP) Review

ARP is a protocol used for resolving IP addresses to MAC addresses. The main issue is that although IP addresses are used to forward IP packets across networks, a link-level address of the host or router to which you want to send the packet is required in a particular physical network. Therefore, hosts in the network need to keep a mapping between IP and link-layer addresses. Hosts can use ARP to broadcast query messages for a particular IP address in their physical networks so that the appropriate host can reply this query with its link-layer address.