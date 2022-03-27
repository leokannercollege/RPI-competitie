from datetime import datetime
from scapy.all import sniff, Dot11ProbeReq
import logging
import time
import json
import random
from gpiozero import LED
from rgbstrip import LEDStrip
from collections import Counter

IGNORE_LIST = set(['00:00:00:00:00:00', '01:01:01:01:01:01', '02:02:02:02:02:02', '03:03:03:03:03:03', '04:04:04:04:04:04']) #5 werknemers
SEEN_DEVICES = {} #aantal bezoekers bij bij een wachtlocatie

CLK = 18 #yellow
DAT = 17 #white

#zet het rgb-lampje op neutraal (uit)
strip = LEDStrip(CLK, DAT)
strip.setcolouroff()


with open("devices.json", "r") as f:    
    known_devices = json.load(f)

with open("visitors.json", "r") as g:
    visitors = json.load(g) 

# functie om live mac-addressen te verwerken
def handle_packet(pkt):
    if not pkt.haslayer(Dot11ProbeReq):
        return
    if pkt.type == 0 and pkt.subtype == 4: 
        curmac = pkt.addr2
        curmac = curmac.upper() 
        #print (curmac)
        show_hologram(curmac)
     
       
def show_hologram(curmac):               
    if curmac not in IGNORE_LIST: #negeer als de device van een mederwerker is        
        if curmac in known_devices:
            #logging.info('Probe Recorded from ' +  known_devices[curmac] + ' with MAC ' + curmac)
            global SEEN_DEVICES
            SEEN_DEVICES[curmac] = known_devices[curmac]             
        else:
            #logging.info(' Probe Recorded from MAC ' + curmac )
            SEEN_DEVICES[curmac] = "overig"
        
        # doe een actie als er meer dan 10 devices bij een wachtlocatie zijn
        if len(SEEN_DEVICES) > 10 :
            count_devices = Counter(SEEN_DEVICES.values())
            print(count_devices)
            group = max(count_devices, key=count_devices.get)
            
            if group == 'overig':
                del count_devices['overig']
                group = max(count_devices, key=count_devices.get)
                print(count_devices)
           
            if group == "kleuters":
                strip.setcolourrgb(0, 255, 0)
                time.sleep(10)
                strip.setcolouroff()
            elif group == "tieners":
                strip.setcolourrgb(255, 0, 0)
                time.sleep(10)
                strip.setcolouroff()
            elif group == "adolescenten":
                strip.setcolourrgb(0, 0, 255)
                time.sleep(10)
                strip.setcolouroff()
            # reset de telling na de show
            SEEN_DEVICES = {}
        
'''met sniffer'''    
# def main():     
#     logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',filename='wifiscanner.log',level=logging.DEBUG) #setup logging to file
#     logging.info('Wifi Scanner Initialized') 
#     print('\n' + '\033[93m' + 'Wifi Scanner Initialized' + '\033[0m' + '\n') 
#     
#     import argparse
#     parser = argparse.ArgumentParser()
#     parser.add_argument('--interface', '-i', default='wlan1', # Change mon0 to your monitor-mode enabled wifi interface
#                 help='monitor mode enabled interface')
#     args = parser.parse_args()


#     sniff(iface=args.interface, prn=handle_packet) #start sniffin
#     while 1:
#        time.sleep(1)

'''met simulatie-data'''
def main():    
    while True:
        show_hologram(random.choice(visitors))
        time.sleep(1)

if __name__ == '__main__':
    main()
