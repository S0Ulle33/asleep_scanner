import logging
import time


combinations = []
top_logopass = {}
working_hosts = []
random_countries = []
snapshots_counts = 0
custom_brute_file = False
snapshots_enabled = True
ch_count = 0
max_ips = 0
index = 0
total = 0
state = 0.0

global_country = ''
global_ports = ["37777"]

tmp_masscan_file = 'res_scan.txt'
logins_file = 'logins.txt'
passwords_file = 'passwords.txt'
logopass_file = 'combinations.txt'
results_file = 'results_%s.csv'
ips_file = 'ips_%s.txt'
xml_file = 'smart_pss_%s.xml'

snapshots_folder = "tmp_snapshots"
reports_folder = "reports"

# FIX HERE MASSCAN LOCATION
masscan_windows_path = 'masscan.exe'
masscan_nix_path = 'masscan'

# WRITE HERE MASSCAN ARGUMENTS

def additional_masscan_params():
	masscan_params = '--randomize-hosts -sS' # add interface here to avoid manual input
	if "-e" in masscan_params:
		return masscan_params
	else:
		tunnel = input('''\nPlease enter your VPN Tunnel interface
[WARNING] Add interface to config.py to avoid manual input\n\nLeave empty if none: ''')
	if tunnel:
		full_masscan_params = masscan_params + f' -e {tunnel}'
		return full_masscan_params
	else:
		return masscan_params

#Ускорение / Perfomance
# SPECIFY HERE SPEED/QUALITY OF SCAN AND BRUTE
default_masscan_threads = 3000
#default_check_threads = 120
default_brute_threads = 160
default_snap_threads = 140
default_image_threads = 60

# SPECIFY HERE CAMERAS COUNT IN SMARTPSS XML
max_xml_entries = 255 # 16 optimum

start_datetime = time.strftime("%Y.%m.%d-%H.%M.%S")

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logging.getLogger("requests").setLevel(logging.INFO)

def update_status():
	global index
	global total
	global state
	index += 1
	state = round(10*(index/total), 2)


