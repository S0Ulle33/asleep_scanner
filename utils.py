import logging
import random
import re
import sys
from pathlib import Path
from shutil import rmtree

import config


def masscan_parse(brute_file):
    with open(brute_file, 'r') as file:
        hosts = []
        q = False
        for line in file.readlines():
            new_ips = re.findall(r'[0-9]+(?:\.[0-9]+){3}', line)
            port_re = re.search(r'tcp (\d+)', line)
            if port_re:
                port = port_re.group(1)
            elif not port_re and config.custom_brute_file:
                port = config.global_ports
            else:
                port = '37777'
            for p in port:
                for ip in new_ips:
                    if config.custom_brute_file:
                        hosts.append([ip, p])
                    else:
                        hosts.append([ip, port])
                        q = True
                if q:
                    break

#        file.seek(0)
#        for hst in hosts:
#            file.write('%s:%s\n' % (hst[0], hst[1]))
#        file.truncate()
    return hosts


def prepare_folders_and_files():
    # Create /tmp_snapshots/ and /tmp_snapshots/trash
    snapshots_folder = Path(config.snapshots_folder)
    if snapshots_folder.exists():
        rmtree(snapshots_folder)
    snapshots_folder.mkdir()
    Path(snapshots_folder / 'trash').mkdir()

    # Create /reports/ and /reports/datetime
    reports_folder = Path(config.reports_folder) / Path(config.start_datetime)
    reports_folder.mkdir(parents=True)


def setup_credentials(use_custom_credentials):
    if use_custom_credentials:
        if not Path(config.logins_file).exists():
            logging.error(f'Logins file {config.logins_file} not found!')
            sys.exit(0)
        if not Path(config.passwords_file).exists():
            logging.error(f'Passwords file {config.passwords_file} not found!')
            sys.exit(0)

        logins = list(map(str.strip, open(config.logins_file).readlines()))
        passwords = list(map(str.strip, open(config.passwords_file).readlines()))

        config.combinations = [(login, password) for login in logins for password in passwords]

        logging.debug(f'Logins loaded: {", ".join(logins)}')
        logging.debug(f'Passwords loaded: {", ".join(passwords)}')
    else:
        if not Path(config.logopass_file).exists():
            logging.error(f'Login/password combinations file {config.logopass_file} not found!')
            sys.exit(0)

        raw_creds = list(map(str.strip, open(config.logopass_file).readlines()))
        for raw_cred in raw_creds:
            login_pass = raw_cred.split(':')
            if len(login_pass) == 2:
                config.combinations.append((login_pass[0], login_pass[1]))
        random.shuffle(config.combinations)

        logging.debug(f'Login/password combinations loaded: {", ".join(raw_creds)}')
