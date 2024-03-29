Overview

In this assignment, you are going to implement the core functionalities of an Ethernet learning switch using the Switchyard framework. An Ethernet switch is a layer 2 device that uses packet switching to receive, process and forward frames to other devices (end hosts, other switches) in the network. A switch has a set of interfaces (ports) through which it sends/receives Ethernet frames. When Ethernet frames arrive on any port, the switch process the header of the frame to obtain information about the destination host. If the switch knows that the host is reachable through one of its ports, it sends out the frame from the appropriate output port. If it does not know where the host is, it floods the frame out of all ports except the input port.

Details

Your task is to implement the logic that is described in the flowchart here. As it is described in the last paragraph of the "Ethernet Learning Switch Operation" section, your switch will also handle the frames that are intended for itself and the frames whose Ethernet destination address is the broadcast address FF:FF:FF:FF:FF:FF.

In addition to these, you will also implement three different mechanisms to purge the outdated/stale entries from the forwarding table. This will allow your learning switch to adapt to changes in the network topology.

These mechanisms are:

Remove the least recently used (LRU) entry from the forwarding table. For this functionality assume that your table can only hold 5 entries at a time. If a new entry comes and your table is full, you will remove the entry that has not been matched with a Ethernet frame destination address for the longest time.
You will implement these mechanisms in three separate Python files. The core functionalities that are explained above will be the same for these implementations.
