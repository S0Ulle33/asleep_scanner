import ipaddress
import logging
import random
import sys
from datetime import datetime

import pytz
import requests
from countrycode import countrycode
from geoip import geolite2

import config


class GeolocationToIp():
    def __init__(self, country, city='', lat='', lng=''):
        self.country = country
        self.city = city
        self.lat = lat
        self.lng = lng
        self.ranges = []
        self.get_ranges()

    def get_ranges(self):
        return True

    def get_random_ranges(self, num=1, max_ips=0):
        return random.choice(self.ranges)

    @staticmethod
    def get_cidr(cidr_range):
        return cidr_range.split('/')[1]

    @staticmethod
    def get_cidr_count(cidr_range):
        return 2**(32-int(GeolocationToIp.get_cidr(cidr_range)))

class IPDenyGeolocationToIP(GeolocationToIp):
    def get_ranges(self):
        code = countrycode.countrycode(codes=[self.country], origin='country_name', target='iso2c')[0]
        resp = requests.get('http://www.ipdeny.com/ipblocks/data/aggregated/{}-aggregated.zone'.format(code.lower()))
        if 'title' in resp.text:
            self.ranges = []
            return False
        self.ranges = [r for r in resp.text.split('\n') if r.strip()]
        return True

    def get_random_ranges(self, num=1, max_ips=0, day_ranges=False):
        if max_ips:
            rranges = []
            ips = 0
            tries = 100
            kill_loop = 0
            while tries != 0:
                r = random.choice(self.ranges)
                if not r.strip():
                    continue
                rcidr = r.split('/')[1]
                count1 = 2**(32-int(rcidr))
                if ips+count1 < max_ips+(max_ips/10):
                     tries -= 1
                else:
                     break
                if r not in rranges and not day_ranges:
                    rranges.append(r)
                    ips += count1
#                    config.max_ips += ips
                    if kill_loop > 1000:
                         break
                    elif ips < max_ips+(max_ips/10) and tries == 1:
                       tries += 2
                       kill_loop += 1
                elif r not in rranges and day_ranges:
                     check = ipaddress.ip_network(r)
                     r_ip = random.randrange(1, 200)
                     c_ip = str(check[r_ip])
                     try:
                         tm = geolite2.lookup(c_ip)
                     except TypeError:
                           print('''Python dependencies error:\n
 ~$ pip3 uninstall python-geoip python-geoip-python3\n ~$ pip3 install python-geoip-python3''')
                           sys.exit(0)
                     try:
                         time_src = pytz.timezone(tm.timezone)
                     except Exception as e:
                         logging.debug(e)
                         continue
                     time_pm = datetime.now(time_src)
                     check_done = time_pm.strftime("%H")
                     pm_0 = range(9)
                     pm_1 = ["{:02d}".format(i) for i in pm_0]
                     pm_1 += ["17","18","19","20","21","22","23"]
                     if [time for time in pm_1 if time in check_done]:
                        continue
                     else:
                        rranges.append(r)
                        ips += count1
                        config.max_ips += ips
#                     elif not rranges and tries == 1:
#                         tries += 1
                     if rranges:
                        config.random_countries.append(self.country)

        else:
            rranges = [random.choice(self.ranges)]
        return rranges
