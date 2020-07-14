### Dahua DVRs bruteforcer at port 37777

The author of this code **is not responsible** for any illegal actions. \
For educational purposes only..

![Terminal record](https://github.com/d34db33f-1007/asleep_scanner/raw/master/tty.gif)

#### Download

Binary available on the [**releases**](https://github.com/d34db33f-1007/asleep_scanner/releases) page

```
USAGE
   $ asleep.py [-h] [-s SCAN_FILE] [-p PORTS] [-b BRUTE_FILE] [-l] [-m] [-t THREADS] [-d]
               [--masscan-resume] [--no-snapshots] [--no-xml] [--dead] [--country] [--random-country]

ARGUMENTS
   -h, --help        show this help message and exit
   -s SCAN_FILE      file with IP ranges to scan, e.g. 192.168.1.1-192.168.11.1
   -p PORTS          ports to scan (default: 37777), e.g. 37777,37778
   -b BRUTE_FILE     file with IPs to brute, in any format
   -l                brute combinations from logins.txt and passwords.txt instead of combinations.txt
   -m, --masscan     run Masscan and brute the results
   -t THREADS        number of thread for Masscan (default: 3000)
   --masscan-resume  continue paused Masscan
   --no-snapshots    don't make snapshots
   --no-xml          don't make SMART PSS .xml files
   --dead            write not bruted cams to dead_cams.txt file
   --country         scan by country
   --random-country  scan by random country
   -d, --debug       debug output

EXAMPLES
   $ ./asleep -m -s ips.txt
   $ ./asleep -m -s ips.txt -p 37777,37778,47777
   $ ./asleep --country
   $ ./asleep --random-country
   $ ./asleep -b ips.txt
```
            
##### Interactive:

* `git clone https://github.com/d34db33f-1007/asleep_scanner.git`
* `pip3 install -r requirements.txt`
* `python3 asleep.py --help`

##### View cams in live:

* Windows / macOS
  * [SmartPSS](https://dahuawiki.com/SmartPSS)
* Linux
  * [TaniDVR](http://tanidvr.sourceforge.net/)

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
