import logging
import random
import re, os

import config

from shutil import rmtree

def masscan_parse(brute_file):
    with open(brute_file, 'r') as file:
        hosts = []
        for line in file: #.readlines():
            new_ips = re.findall(r'[0-9]+(?:\.[0-9]+){3}', line)
            port_re = re.search(r'tcp (\d+)', line)
            port = '37777' if not port_re else port_re.group(1)
            for ip in new_ips:
                hosts.append([ip, port])
    return hosts


def prepare_folders_and_files():
    reports_folder = os.path.join(config.reports_folder, config.start_datetime)
    if not os.path.exists(config.snapshots_folder):
        os.makedirs(config.snapshots_folder)
    else:
        rmtree(config.snapshots_folder)
        os.makedirs(config.snapshots_folder)
    os.mkdir(os.path.join(config.snapshots_folder, 'trash'))
    os.makedirs(reports_folder)
    results_file = os.path.join(reports_folder, config.results_file)
    xml_file = os.path.join(reports_folder, config.xml_file)
    if config.custom_brute_file:
        tmp_masscan_file = os.path.join(reports_folder, config.tmp_masscan_file)

def setup_credentials(use_logopass):
    if use_logopass:
        if os.path.exists(config.logopass_file):
            raw_logins = list(map(str.strip, open(config.logopass_file).readlines()))
            for raw_login in raw_logins:
                login = raw_login.split(':')
                if len(login) == 2:
                    config.logopasses.append(login)

            logging.debug('Login/password combinations loaded: %s' % ", ".join(raw_logins))
            random.shuffle(config.logopasses)
        else:
            logging.error('Login/password combinations file %s not found!' % config.logopass_file)
            exit(-2)
    else:
        if os.path.exists(config.logins_file):
            config.logins = list(map(str.strip, open(config.logins_file).readlines()))
            logging.debug('Logins loaded: %s' % ", ".join(config.logins))
        else:
            logging.error('Logins file %s not found!' % config.logins_file)
            exit(-2)
        if os.path.exists(config.passwords_file):
            config.passwords = list(map(str.strip, open(config.passwords_file).readlines()))
            logging.debug('Passwords loaded: %s' % ", ".join(config.passwords))
        else:
            logging.error('Passwords file %s not found!' % config.passwords_file)
            exit(-2)
