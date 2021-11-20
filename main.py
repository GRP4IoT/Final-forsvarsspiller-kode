import umqtt_robust2
import GPSfunk
import formel
import led_ring_funcs
import network
from machine import Pin, reset
from umqtt_robust2 import MQTTClient
# ATGM336H-5N <--> ESP32 
# GPS til ESP32 kredsløb
# GPS VCC --> ESP32 3v3
# GPS GND --> ESP32 GND
# GPS TX  --> ESP32 GPIO 16
from time import sleep_ms, sleep, ticks_ms
import neopixel
import ujson
station = network.WLAN(network.STA_IF)
station.active(True)
rssi = 0
# aktuator vibrator, G-pin på GND, V-pin på 3v3, S-pin på 2
vibrator = Pin(2, Pin.OUT, value=0)

n = 12 # antallet af RGB lys på LEDringen
p = 17 # Den pin LED-ringen er tilsluttet
np = neopixel.NeoPixel(Pin(p), n) # variablen til at kontrollere LED-ringen
# LED ringens DI pin på ESP pin 17, og LED ringens V5 pin på ESP pin 5V

lib = umqtt_robust2 # variable til lettere at håndtere mqtt biblioteket
led = led_ring_funcs # variable til lettere at håndtere LED funktions biblioteket

# opret en ny feed kaldet map_gps indo på io.adafruit
mapFeed = bytes('{:s}/feeds/{:s}'.format(b'GRP4', b'mapfeed/csv'), 'utf-8')
# opret en ny feed kaldet speed_gps indo på io.adafruit
speedFeed = bytes('{:s}/feeds/{:s}'.format(b'GRP4', b'speedfeed2/csv'), 'utf-8')

distanceforsvar = bytes('{:s}/feeds/{:s}'.format(b'GRP4', b'distanceforsvar/csv'), 'utf-8')

rssi = bytes('{:s}/feeds/{:s}'.format(b'GRP4', b'rssi/csv'), 'utf-8')
# Variabler til at holde styr på om LED funktioner er sket
startUp = False
ledNormBack = False

# vores variabler til net ting
#station = network.WLAN(network.STA_IF)
#ssid = []
#rssi = 0

# forsøg på at implementere non-blocking delay
currentTime = 0.000 # variable til at holde styr på tid
intervalMain = 10000  # intervallet der skal ske noget
previousTimeMain = 0  # sidste gang der skete noget
# vores offside non-block delay variabler
intervalOffside = 11000
previousTimeOffside = 0
# vores netværk skanner non-block delay
intervalPog = 12000
previousTimePog = 0
#Vores reset timer
intervalReset = 12000
previousTimeReset = 0
count = 0

while True:
    #gpsData = GPSfunk.main()
    currentTime = ticks_ms()
    GPSlist = []
    
    if startUp == False:
        startUp = True
        led.power_on()
        sleep(2)
        
    if lib.c.is_conn_issue():
        while lib.c.is_conn_issue():
            led.trying_con() # LED ringen tændes med en bounce funktion
            # hvis der forbindes returnere is_conn_issue metoden ingen fejlmeddelse
            lib.c.reconnect()
        else:
            led.trying_con() # LED ringen tændes med en bounce funktion
            lib.c.resubscribe()
    try:

        
        if currentTime - previousTimeMain >= intervalMain:
            previousTimeMain = currentTime
            #åben data_rssi.ujson filen
            a_file = open("data_rssi.ujson", "r")
            a_json = ujson.load(a_file)
            pretty_json = ujson.dumps(a_json,)
            a_file.close()
            print(type(pretty_json))
            lib.c.publish(topic=rssi, msg=pretty_json)
            led.uploading()
            gpsData = GPSfunk.main()
            ledNormBack = True
            lib.c.publish(topic=mapFeed, msg=gpsData[0])
            speed = gpsData[0]
            speed = speed[:4]
            lib.c.publish(topic=speedFeed, msg=speed)
            #print("speed: ",speed)
            GPSlist.append(float(gpsData[1]))
            GPSlist.append(float(gpsData[2]))
            count +=1
            if count >= 1:
                latA = GPSlist[0]
                lonA = GPSlist[1]
                GPScoord1 = latA, lonA
                latB = 55.70656
                lonB = 12.53932
                GPScoord2 = latB, lonB
                distance = formel.afstand(GPScoord1, GPScoord2)
                print(distance,'forsvar distance')
                lib.c.publish(topic=distanceforsvar, msg=str(distance))         
        
        if currentTime - previousTimePog >= intervalPog:
            previousTimePog = currentTime
            station.disconnect();
            print("disconnected")
            ssid = station.scan()
            for i in ssid:
                if i[0] == b'LTE-1857':
                    print(i)
                    rssi = i[3]
                    print(rssi)
            #Send rssi value til data_rssi.ujson filen        
            with open('data_rssi.ujson', 'w') as f:
                ujson.dump(rssi, f)

        if currentTime - previousTimeReset >= intervalReset:
            previousTimeReset = currentTime
            print("resetter")
            reset()

        if ledNormBack == True:
            ledNormBack = False
            #print("back to normal")
            led.power_on()
        
    # Stopper programmet når der trykkes Ctrl + c
    except KeyboardInterrupt:
        print('Ctrl-C pressed...exiting')
        led.clear()
        #sleep(1)
        lib.c.disconnect()
        lib.wifi.active(False)
        lib.sys.exit()
    except OSError as e:
        print('Failed to read sensor.')
    except NameError as e:
        print('NameError', e)
    except TypeError as e:
        print('TypeError', e)
    
    lib.c.check_msg() # needed when publish(qos=1), ping(), subscribe()
    lib.c.send_queue()  # needed when using the caching capabilities for unsent messages

lib.c.disconnect()