import urllib.request
import xml.etree.ElementTree as ET
import html

url1 = "https://xml.buienradar.nl/"
url2 = "https://gadgets.buienradar.nl/data/raintext?lat={lat:.2f}&lon={lon:.2f}"


def val_to_rain(x):
    '''The buienradar formula to convert their raindata to mm/u
    https://www.buienradar.nl/overbuienradar/gratis-weerdata
    '''
    return 10**((x-109)/32)

def get_rain_data(lat, lon):
    text = urllib.request.urlopen(url2.format(lat=lat,lon=lon)).read().decode('utf-8')
    rains = []
    times = []
    for l in text.splitlines():
        r,t = l.split('|')
        rains.append(int(r))
        times.append(t)
    return rains,times

def parse_rain_data(rains):
    if not any(rains):
        return "Het is droog de komende twee uur"
    drycount = 0
    for r in rains:
        if r: break
        drycount += 1

    if drycount*5>90:
        return "Het is droog de komende anderhalf uur"

    avgrain = sum(val_to_rain(x) for x in [rains[drycount],rains[drycount+1],rains[drycount+2],rains[drycount+3]])/4 #average rain over 20 minute period

    if avgrain<0.5: descr = "motregenen"
    elif avgrain<2: descr = "zacht regenen"
    elif avgrain<10: descr = "regenen"
    elif avgrain<30: descr = "flink regenen"
    elif avgrain<80: descr = "onweren"
    else: descr = "super hard onweren"

    if drycount==0 and avgrain<0.5:
        return "Het is aan het miezeren"
    if drycount==0 and avgrain<5:
        return "Het is zacht aan het regenen"
    if drycount==0 and avgrain<20:
        return "Het is aan het regenen"
    if drycount==0 and avgrain<60:
        return "Het is echt heel hard aan het regenen"
    if drycount==0:
        return "Blijf maar gewoon binnen. Het is een echte stortbui"

    if drycount*5>=60:
        return "Het blijft het komende uur nog wel droog, daarna gaat het %s" % descr
    return "Het is de komende %d minuten droog, daarna gaat het %s" % (drycount*5, descr)
    
    
    

def raw_weather_report(weerstation = "6275", lat = 51.81, lon = 5.85):
    '''Returns (temperature, rain forecast, weather report

    Default weather station is Arnhem (6275), and lattitude and longitude is in Nijmegen'''
    text = urllib.request.urlopen(url1).read()
    xml = ET.fromstring(text) #buienradarnl
    root = xml[0] #weergegevens
    ac = root.find("actueel_weer")
    we = ac.find("weerstations")
    station = [i for i in we if i.attrib['id']==weerstation][0]
    temp = station.find("temperatuurGC").text #temperatuur nu in graden
    samenvatting = html.unescape(root.find("verwachting_vandaag").find("samenvatting").text)

    rains, times = get_rain_data(lat,lon)
    buien = parse_rain_data(rains)

    return temp, buien, samenvatting

def weather_report(weerstation = "6275", lat = 51.81, lon = 5.85):
    temp, buien, samenvatting = raw_weather_report(weerstation, lat, lon)

    return samenvatting + " Het is nu %s graden buiten. %s" % (temp, buien)
