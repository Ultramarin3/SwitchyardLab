#!/usr/bin/env python3

from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.userlib import *
from random import randint
import time

ENDIAN='big'

class WindowEntry:
    # WindowEntry is used to track sent pkts attributes, like time of the initial
    # transmission, time of the last [re]transmission, and the sequence number
    def __init__(self, seq_num, ack=False, ts_initial=None, ts_last=None):
        self.seq_num = seq_num
        self.ack = ack
        if ts_initial == None:
            self.ts_initial = time.time()
        if ts_last == None:
            self.ts_last = time.time()

def print_output(total_time, num_ret, num_tos, throughput, goodput, estRTT, TO, min_rtt, max_rtt):
    print("Total TX time (s): " + str(total_time))
    print("Number of reTX: " + str(num_ret))
    print("Number of coarse TOs: " + str(num_tos))
    print("Throughput (Bps): " + str(throughput))
    print("Goodput (Bps): " + str(goodput))
    print("Final estRTT(ms): " + str(estRTT))
    print("Final TO(ms): " + str(TO))
    print("Min RTT(ms):" + str(min_rtt))
    print("Max RTT(ms):" + str(max_rtt))


def main(net):
    global blastee_ip
    global total_packet_to_blast
    global length_per_blast
    global window_size
    global estRTT
    global recv_timeout_ms
    global ewma_alpha
    my_intf = net.interfaces()
    mymacs = [intf.ethaddr for intf in my_intf]
    myips = [intf.ipaddr for intf in my_intf]
    cont = open('./blaster_params.txt',"r")
    for line in cont.readlines():
        value = line.split()
        blastee_ip = value[1]
        total_packet_to_blast = int(value[3])
        length_per_blast = int(value[5])
        window_size = int(value[7])
        estRTT = float(value[9])
        recv_timeout_ms = float(value[11])
        ewma_alpha = float(value[13])
    
    if len(my_intf) != 1:
        raise Exception("Blaster must have exactly one interface!")
    intf = my_intf[0]
    target_ethaddr = EthAddr('40:00:00:00:00:01') # see start_mininet.py
    blast_content = b'\xff' * length_per_blast
    TO = 2*estRTT
    window = [None for i in range(window_size)]
    lhs = 1
    rhs = 1
    metrics_first_sent_time = None
    metrics_last_ack_time = None
    num_ret = 0
    num_tos = 0
    num_payload = 0
    min_rtt = None
    max_rtt = None
    while True:
        if rhs > total_packet_to_blast and lhs == rhs:
            print_output(metrics_last_ack_time-metrics_first_sent_time, num_ret, num_tos, num_payload/(metrics_last_ack_time-metrics_first_sent_time), (total_packet_to_blast*length_per_blast)/(metrics_last_ack_time-metrics_first_sent_time),estRTT,TO, min_rtt, max_rtt)
            print("here")
            return

        for offset in range(rhs - lhs):
            seq = lhs + offset
            now = time.time()
            window_entry = window[seq%window_size]
            if window_entry.ack:
                continue 
            age_s = now - window_entry.ts_last
            if age_s*1000 > TO:
                etp = Ethernet(src = intf.ethaddr,dst = target_ethaddr)
                ip = IPv4(
                    protocol = IPProtocol.UDP,
                    src = intf.ipaddr,
                    dst = blastee_ip,
                    ttl = 64
                )
                pkt = etp + ip + UDP() + seq.to_bytes(4, ENDIAN) + length_per_blast.to_bytes(2, ENDIAN) + blast_content
                try:
                    net.send_packet(intf.name, pkt)
                    num_payload += length_per_blast
                    if metrics_first_sent_time == None:
                        metrics_first_sent_time = time.time()
                except ValueError as e:
                    log_debug("Failed to send packet due to ValueError: {}".format(str(e)))
                except:
                    log_debug("Failed to send packet due to error: {}".format(sys.exc_info()[0]))
                
                
                window[seq%window_size].ts_last = now
                num_ret += 1
                num_tos += 1
                log_info("Retransmitted seq {}.".format(seq))

        cnt = window_size - (rhs - lhs)
        if cnt > 0:
            for _ in range(cnt):
                if rhs <= total_packet_to_blast:
                    etp = Ethernet(src = intf.ethaddr, dst = target_ethaddr)
                    ip = IPv4(
                        protocol = IPProtocol.UDP,
                        src = intf.ipaddr,
                        dst = blastee_ip,
                        ttl = 64
                    )
                    pkt = etp + ip + UDP() + rhs.to_bytes(4, ENDIAN) + length_per_blast.to_bytes(2, ENDIAN) + blast_content
                    try:
                        net.send_packet(intf.name, pkt)
                        num_payload += length_per_blast
                        if metrics_first_sent_time == None:
                            metrics_first_sent_time = time.time()
                    except ValueError as e:
                        log_debug("Failed to send packet due to ValueError: {}".format(str(e)))
                    except:
                        log_debug("Failed to send packet due to error: {}".format(sys.exc_info()[0]))
                
                    window[rhs%window_size] = WindowEntry(rhs)
                    log_debug("blasted pkt with seq # of {}".format(rhs))
                    rhs += 1
       
        try:
            _, _, pkt = net.recv_packet(timeout=recv_timeout_ms/1000.0)
        except NoPackets:
            log_debug("No packets available in recv_packet")
            continue
        except Shutdown:
            log_debug("Got shutdown signal")
            break
            
        contents = pkt.get_header(RawPacketContents)
        if contents == None:
            log_debug('Ignored packet of unknown type')
            return
        now = time.time()
        seq_num = int.from_bytes(contents.data[:4], ENDIAN)
        if seq_num >= lhs and seq_num <= rhs:
            log_debug('Received ACK for seq # {}'.format(seq_num))
            window[seq_num%window_size].ack = True
            metrics_last_ack_time = now
            rtt_ms = (now - window[seq_num%window_size].ts_initial) * 1000
            if min_rtt == None or rtt_ms < min_rtt:
                min_rtt = rtt_ms
            if max_rtt == None or rtt_ms > max_rtt:
                max_rtt = rtt_ms
      
            estRTT = (  ((1-ewma_alpha)*estRTT)+(ewma_alpha*rtt_ms)  )
            TO = 2*estRTT
        
        while window[lhs%window_size].ack and lhs < rhs:
            lhs += 1
    net.shutdown()
    
    
    

