import urllib.request
from ogn.parser import parse, ParseError
from ogn.client import AprsClient
from datetime import datetime
from datetime import timedelta
import threading
import socket
import math
import time
import requests

global glider_ICAO
global APRSbeacon
global traffic_list



class aircraft():
    def __init__(self):
        self.id = ""
        self.id_ADSB = ""
        self.id_OGN = ""
        self.callsign_ADSB = ""
        self.callsign_OGN = ""
        self.timelast_ADSB = 0
        self.timelast_OGN = 0
        self.lat_ADSB = 0
        self.lat_OGN = 0
        self.lon_ADSB = 0
        self.lon_OGN = 0
        self.alt_ADSB = 0
        self.speed_ADSB = 0
        self.speed_OGN = 0
        self.heading_ADSB = 0
        self.heading_OGN = 0
        self.climb_ADSB = 0
        self.climb_OGN = 0
        self.type_ADSB = 'GLID'

def getADSB():
    '''this function gets ADSB data for gliders and adds it to the traffic_list'''
    global traffic_list
    time.sleep(35)
    print('\nConnecting to ADSBexchange')
    url = "https://adsbexchange.com/api/aircraft/v2/sqk/1202/"    #requests url
    headers = {
    'api-auth': "####", #api key given by ADSBExchange
    'accept-encoding': "gzip"    
    }   # requests headers
    while True:
        try:
            response = requests.request("GET", url, headers=headers)    #requests response
            ADSBaircraft = response.json()   #assign response to JSON object
            num_ac = ADSBaircraft['total']   #get number of aircraft in response packet
            print('\nnumber of ADSBExchange api aircraft sqwk 1202:', num_ac)
        except Exception as e:
            print("exception at GET ADSBExchange API request")
            print(e)
            pass
        
        for i in range(num_ac):
            try:
                #print('aircraft num',i)
                glider = aircraft()
                glider.id = ADSBaircraft['ac'][i]['hex']                    #icao hex
                glider.id_ADSB = ADSBaircraft['ac'][i]['hex']               #icao hex
                glider.callsign_ADSB = ADSBaircraft['ac'][i]['flight']      #N number
                glider.timelast_ADSB = int(str(ADSBaircraft['ctime'])[:10]) #10 digit unix time
                glider.lat_ADSB = round(ADSBaircraft['ac'][i]['lat'],4)     #4 digit latitude ie 40.0437
                glider.lon_ADSB = round(ADSBaircraft['ac'][i]['lon'],4)     #4 digit longitude ie -105.2402
                try:
                    glider.alt_ADSB = ADSBaircraft['ac'][i]['alt_baro']         #ft
                except:
                    pass
                try:
                    glider.alt_ADSB = ADSBaircraft['ac'][i]['alt_geom']         #ft
                except:
                    pass
                try:
                    glider.speed_ADSB = round(ADSBaircraft['ac'][i]['gs'])      #kt
                except:
                    pass
                try:
                    glider.heading_ADSB = round(ADSBaircraft['ac'][i]['track'])        #deg
                except:
                    pass                
                try:
                    glider.climb_ADSB = ADSBaircraft['ac'][i]['baro_rate']      #feet/min
                    #print('baro',glider.climb_ADSB)
                except:
                    pass
                try:
                    glider.climb_ADSB = ADSBaircraft['ac'][i]['geom_rate']      #feet/min
                    #print('geom',glider.climb_ADSB)
                except:
                    pass
                try:
                    glider.type_ADSB = ADSBaircraft['ac'][i]['t']      #type 'GLID' for glider
                except:
                    pass
                print(i+1,') ',glider.id, 'type:',glider.type_ADSB,'reg:',glider.callsign_ADSB,'at:', glider.lat_ADSB,glider.lon_ADSB,'alt:',glider.alt_ADSB,'spd:',glider.speed_ADSB,'trk:',glider.heading_ADSB,'clb:',glider.climb_ADSB)
                
                
                seen = False
                for x, item in enumerate(traffic_list): #add gliders to traffic list, update if they already exist
                    if item.id == glider.id:
                        traffic_list[x].id = glider.id
                        traffic_list[x].id_ADSB = glider.id_ADSB
                        traffic_list[x].callsign_ADSB = glider.callsign_ADSB
                        traffic_list[x].timelast_ADSB = glider.timelast_ADSB
                        traffic_list[x].lat_ADSB = glider.lat_ADSB
                        traffic_list[x].lon_ADSB = glider.lon_ADSB
                        traffic_list[x].alt_ADSB = glider.alt_ADSB
                        traffic_list[x].speed_ADSB = glider.speed_ADSB
                        traffic_list[x].heading_ADSB = glider.heading_ADSB
                        traffic_list[x].climb_ADSB = glider.climb_ADSB
                        traffic_list[x].type_ADSB = glider.type_ADSB
                        #print("id",traffic_list[x].id)                          
                        #print("id_ADSB",traffic_list[x].id_ADSB)                          
                        #print("callsign_ADSB",traffic_list[x].callsign_ADSB)                           
                        #print("timelast_ADSB",traffic_list[x].timelast_ADSB)                          
                        #print("lat_ADSB",traffic_list[x].lat_ADSB)                           
                        #print("lon_ADSB",traffic_list[x].lon_ADSB)                           
                        #print("alt_ADSB",traffic_list[x].alt_ADSB)
                        #print("speed_ADSB",traffic_list[x].speed_ADSB)
                        #print("heading_ADSB",traffic_list[x].heading_ADSB)
                        #print("climb_ADSB",traffic_list[x].climb_ADSB)
    
                        seen = True
                        break
                if not seen:
                    traffic_list.append(glider)
            except Exception as e:
                print(i+1,') ',glider.id,e,'<- parameter missing from ADSBExchange JSON')
                #print('<- error in parsing JSON from ADSBExchange - missing parameter above')
                pass
        time.sleep(9.89) #access the ADSBExchange API every 10 secs
    
    
    

def getOGN():
    '''this function gets OGN data from the OGN APRS server and adds it to the traffic_list'''
    global APRSbeacon
    global traffic_list
    while True:
        try:
            packet_b = sock_file.readline().strip()
            packet_str = packet_b.decode(errors="replace")
            APRSbeacon = parse(packet_str)
            
            #assign incoming beacon packet to glider object
            gliderOGN = aircraft()
            gliderOGN.aprs_type = APRSbeacon["aprs_type"]
            gliderOGN.id = APRSbeacon["name"][3:].lower()  #get lowercase right 6 digits (icao hex)
            gliderOGN.id_OGN = APRSbeacon["name"]  #get lowercase right 6 digits (icao hex)
            gliderOGN.alt_OGN = int(round(APRSbeacon["altitude"]*3.28,0))         # in feet
            gliderOGN.callsign_OGN = APRSbeacon["name"]
            gliderOGN.climb_OGN = int(round(APRSbeacon["climb_rate"]*196.85,0)) #ft/min maybe
            gliderOGN.heading_OGN = int(round(APRSbeacon["track"],0))                    # in degrees
            gliderOGN.lat_OGN = round(APRSbeacon["latitude"],5)                   # 1 meter accuracy
            gliderOGN.lon_OGN = round(APRSbeacon["longitude"],5)                 # 1 meter accuracy
            gliderOGN.speed_OGN = int(round(APRSbeacon["ground_speed"]*.54,1))  # in knots
            gliderOGN.ageRaw_OGN = int((APRSbeacon["timestamp"]- timedelta(hours=7) ).timestamp())#     #local time            
            
            seen = False
            for x, item in enumerate(traffic_list): #add gliders to traffic list, update if they already exist
                if item.id == gliderOGN.id:
                    traffic_list[x].id = gliderOGN.id
                    traffic_list[x].id_OGN = gliderOGN.id_OGN
                    traffic_list[x].alt_OGN = gliderOGN.alt_OGN
                    traffic_list[x].callsign_OGN = gliderOGN.callsign_OGN
                    traffic_list[x].climb_OGN = gliderOGN.climb_OGN
                    traffic_list[x].heading_OGN = gliderOGN.heading_OGN
                    traffic_list[x].lat_OGN = gliderOGN.lat_OGN
                    traffic_list[x].lon_OGN = gliderOGN.lon_OGN
                    traffic_list[x].speed_OGN = gliderOGN.speed_OGN
                    traffic_list[x].timelast_OGN = gliderOGN.ageRaw_OGN
                    #print("timelast_OGN",traffic_list[x].timelast_OGN)

                    seen = True
                    break
            if not seen:
                traffic_list.append(gliderOGN) 
                
            time.sleep(.01)
        except Exception as e:
            #print(e)
            pass
        except:
            pass

def APRS_lat(lat_f):
    '''input latitude as DD.DDDD as int'''
    '''returns latitude as DDMM.MM as a string formatted for APRS'''
    '''only works in north america by design'''
    #get decimal
    lat_d = math.trunc(lat_f)
    #get minutes and get N or S
    if lat_d > 0:
        lat_m = round((lat_f*60) % 60,2)
    else:
        lat_m = round((lat_f*-1*60) % 60,2)
        lat_d = abs(lat_d)

    lat_s = str(lat_d)
    lat_m_s = "{:.2f}".format(lat_m)
    lat_m_afterDec = lat_m_s[-2:]
    #isolate minutes only
    lat_m_o = str(int(lat_m))
    lat_m_o = lat_m_o.zfill(2)
    #combine them
    lat_c = lat_s + lat_m_o + '.' + lat_m_afterDec
    return lat_c

def APRS_lon(lon_f):
    '''input longtidue as DDD.DDDD as int'''
    '''returns latitude as DDDMM.MM as a string formatted for APRS'''
    '''only works in north america by design'''
    #get decimal
    lon_d = math.trunc(lon_f)
    #get minutes and get E or W
    if lon_d > 0:
        lon_m = round((lon_f*60) % 60,2)
    else:
        lon_m = round((lon_f*-1*60) % 60,2)
        lon_d = abs(lon_d)

    lon_s = str(lon_d)
    if abs(lon_d) <100:
        lon_s = lon_s.zfill(3)
    lon_m_s = "{:.2f}".format(lon_m)
    lon_m_afterDec = lon_m_s[-2:]
    #isolate minutes only
    lon_m_o = str(int(lon_m))
    lon_m_o = lon_m_o.zfill(2)
    #combine them
    lon_c = lon_s + lon_m_o + '.' + lon_m_afterDec
    return lon_c


traffic_list = []
startTime = time.time()


#start ADSB listen thread
ADSBThread = threading.Thread(target=getADSB)
ADSBThread.daemon = True
ADSBThread.start()

#start OGN listen thread
OGNThread = threading.Thread(target=getOGN)
OGNThread.daemon = True
OGNThread.start()

#####-----connect to to the APRS server
APRS_SERVER_PUSH = 'glidern2.glidernet.org'
APRS_SERVER_PORT =  14580 #10152
APRS_USER_PUSH = 'ADSBex'
BUFFER_SIZE = 1024
APRS_FILTER = 'g/ALL'

print('Connecting to OGN APRS server')
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((APRS_SERVER_PUSH, APRS_SERVER_PORT))
sock_file = sock.makefile('rb')

data = sock.recv(BUFFER_SIZE)
print("APRS Login reply:  ", data) #server response


#####-----login to APRS server
login = 'user ADSBex pass 9404 vers ADSBExchangeToOGN v0.3 filter r/33/-112/4500 \n'
login = login.encode(encoding='utf-8', errors='strict')
sock.send(login)

data = sock.recv(BUFFER_SIZE)
print("APRS Login reply:  ", data) #server response


#send traffic_list to APRS server periodically
while True:
    #timers#
    timer_now = time.time()
    timer = timer_now - startTime
    fiveMinuteTimer = timer % 300   #300 seconds in 5 min, if >299.9 then action
    threeMinuteTimer = timer % 180   #180 seconds in 3 min, if >179.9 then action
    twentySecondTimer = timer % 20   #20 seconds in 20s, if >19.9 then action 
    tenSecondTimer = timer % 10   #10 seconds in 10s, if >9.9 then action
    fiveSecondTimer = timer % 5   #5 seconds in 5s, if >4.9 then action 
    timenow = datetime.utcnow().strftime("%H%M%S")


    #remove ADSB objects that are known to be not 'GLID' type:
    for m in range(len(traffic_list)):
        if traffic_list[m].type_ADSB != 'GLID' and traffic_list[m].type_ADSB != 'DIMO': #GLID is glider, DIMO is hk36 motorglider...more?
            print(traffic_list[m].id_ADSB,traffic_list[m].type_ADSB,"Not type 'GLID', removing at",datetime.now())
            traffic_list.pop(m)
            break

    #remove ADSB objects that are not in North America:
    for m in range(len(traffic_list)):
        if traffic_list[m].lat_ADSB < -1 or traffic_list[m].lat_ADSB > 60 or traffic_list[m].lon_ADSB < -130 or traffic_list[m].lon_ADSB > 1:
            print(traffic_list[m].id_ADSB,traffic_list[m].lat_ADSB,traffic_list[m].lon_ADSB,'Outside North America, removing at',datetime.now())
            traffic_list.pop(m)
            break

    #remove ADSB objects older than 60 seconds:
    for m in range(len(traffic_list)):
        dt = int(time.time()) - traffic_list[m].timelast_ADSB
        traffic_list[m].timeDiff_ADSB = dt
        #print('timediff (age of signal):',traffic_list[m].timeDiff)
        if traffic_list[m].timeDiff_ADSB > 60 and traffic_list[m].timeDiff_ADSB < 100000: #remove old ADSB objects but don't touch objects that have no time
            print(traffic_list[m].id_ADSB,traffic_list[m].id_OGN,'ADSB missing for more than 60 seconds, removing at',datetime.now())
            traffic_list.pop(m)
            break
        
    #remove OGN objects older than 60 seconds:
    for m in range(len(traffic_list)):
        dt = int(time.time()) - traffic_list[m].timelast_OGN
        traffic_list[m].timeDiff_OGN = dt
        #print('timediff (age of signal):',traffic_list[m].timeDiff)
        if traffic_list[m].timeDiff_OGN > 60 and traffic_list[m].timeDiff_OGN < 100000: #remove old OGN objects but don't touch objects that have no time
            print(traffic_list[m].id_ADSB,traffic_list[m].id_OGN,'OGN missing for more than 60 seconds, removing at',datetime.now())
            traffic_list.pop(m)
            break
	
	#encode and send to APRS server
    if tenSecondTimer > 9.9: #9.9, 10 second timer
        print('\ntraffic list length:',len(traffic_list),'*************','Local time:',datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),'Uptime:',int(timer//3600),'hours',int((timer%3600)//60),'minutes',int((timer%3600)%60),'seconds')
        for n in range(len(traffic_list)):
            #print traffic list for sanity
            print(n+1,'--', 'ADSB:',traffic_list[n].id_ADSB,'OGN:',traffic_list[n].id_OGN,
                  'ADSB time:',traffic_list[n].timelast_ADSB,'OGN time:',traffic_list[n].timelast_OGN,
                  'ADSB lat:',traffic_list[n].lat_ADSB,'OGN lat:',traffic_list[n].lat_OGN,
                  'ADSB lon:',traffic_list[n].lon_ADSB,'OGN lon:',traffic_list[n].lon_OGN,
                  'ADSB hdg:',traffic_list[n].heading_ADSB,'OGN hdg:',traffic_list[n].heading_OGN,
                  'ADSB spd:',traffic_list[n].speed_ADSB,'OGN spd:',traffic_list[n].speed_OGN,
                  'ADSB climb:',traffic_list[n].climb_ADSB,'OGN climb:',traffic_list[n].climb_OGN
                  )

            #format for APRS OGN servers
            if traffic_list[n].timelast_ADSB - traffic_list[n].timelast_OGN > 120: #OGN signal is older than ADSB by 120 seconds, or OGN does not exist
                try:
                    if traffic_list[n].id_OGN[:3] == 'FLR':
                        ICAO = 'FLR' + traffic_list[n].id.upper() # FLR or ICA depending on traffic_list[n].id_OGN
                    else:
                        ICAO = 'ICA' + traffic_list[n].id.upper() # FLR or ICA depending on traffic_list[n].id_OGN
                    
                    APRS_stuff = '>APRS,qAS,ADSBExch:/'
                    time_UTC = datetime.utcfromtimestamp(traffic_list[n].timelast_ADSB).strftime("%H%M%S")
                    lat = APRS_lat(traffic_list[n].lat_ADSB) + 'N'
                    lon = APRS_lon(traffic_list[n].lon_ADSB) + 'W'
                    ac_type = "'"
                    heading = str(int(traffic_list[n].heading_ADSB))           
                    speed = int(traffic_list[n].speed_ADSB)
                    speed = "{:03d}".format(speed)
                    alt = int(traffic_list[n].alt_ADSB)
                    alt = "{:06d}".format(alt)
                    
                    if traffic_list[n].id_OGN[:3] == 'FLR':
                        ICAO_id = 'id06'+ ICAO[3:] #id05 for ICA - id06 for FLR depending on traffic_list[n].id_OGN
                    else:
                        ICAO_id = 'id05'+ ICAO[3:] #id05 for ICA - id06 for FLR depending on traffic_list[n].id_OGN
                    
                    if traffic_list[n].climb_ADSB > 0:
                        climb = ' +' + str(traffic_list[n].climb_ADSB)
                    elif traffic_list[n].climb_ADSB < 0:
                        climb = ' ' + str(traffic_list[n].climb_ADSB)
                    else:
                       climb = ' +0'
                       
                    turn = ' +' + '0.0' 
                    sig_stren = ' ' + '0.0' 
                    errors = '0e'
                    offset = '+' + '0.0' 
                    gps_stren = ' gps2x3'
                    newline = '\n'
                except Exception as e:
                    print(e)
                    pass
                
                #Sanity check for encoded APRS OGN data
                if lat != '0' and lon != '0':
                    try:
                        encode_ICAO = str(ICAO + '>APRS,qAS,ADSBExch:/' + time_UTC + 'h' + lat + '/' + lon + ac_type + heading + '/' + speed + '/' + 'A=' + alt + ' !W00! ' + ICAO_id + climb + 'fpm' + turn + 'rot' + sig_stren + 'dB ' + errors + ' ' + offset + 'kHz' + gps_stren + newline)
                        print('**sending data:',encode_ICAO.strip())
                    
                        #Encode and send to APRS servers
                        sock.send(encode_ICAO.encode())
                        #time.sleep(.02)
                        #sock.send(encode_ICAO.encode())
                    except Exception as e:
                        print(e,'error encoding')
                        pass
                sock.close()

    #keepalive to APRS server (kicks after 30 mins if not)	
    if fiveMinuteTimer > 299.9: #300 second (5 minute) timer
        try:
            sock.send('#keepalive\n'.encode())
	    print('Sending #keepalive')
        except Exception as e:
            print(e,'error keepalive')
            pass

    time.sleep(.09)

