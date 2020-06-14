### Dahua DVRs bruteforcer at port 37777

![Terminal record](https://github.com/d34db33f-1007/asleep_scanner/raw/master/tty.gif)

#### Usage:

1. get ur binary from [**releases**](https://github.com/d34db33f-1007/asleep_scanner/releases) page
   1.  `./asleep_xN --help`

##### Interactive:

*  `git clone https://github.com/d34db33f-1007/asleep_scanner.git`
*  `pip3 install -r requirements.txt`
*  `python3 asleep.py --help`

#### Requirements:
besides content of **requirements.txt** this code needs [**masscan**](https://github.com/robertdavidgraham/masscan) and **Python 3.7 >**

#### Build:

1. get [normal](https://github.com/d34db33f-1007/asleep_scanner/releases/download/14.3b/build.tar.gz) or [light](https://github.com/d34db33f-1007/asleep_scanner/releases/download/14.3b/light_build.tar.gz) build version from [releases](https://github.com/d34db33f-1007/asleep_scanner/releases) page
2. `pip3 install -r requirements.txt`
3. run interactive for testing purposes
4. `pyinstaller --add-data '/path/to/python3.7/site-packages/pyfiglet:./pyfiglet' --add-data '/path/to/python3.7/site-packages/_geoip_geolite2:./_geoip_geolite2' --onefile asleep.py`

#### Configs:

all configs are well commented in .config file.
also check halp with running `./asleep --help`


code can post snapshots to your telegram channel at the end of scanning.
add your Telegram Bot API Key and channel ID in .config file to make this work.

author of this code is not responsible of any illegal actions.
for educational purposes only ;)
