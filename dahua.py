#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import re
import socket
import struct
import time
import logging
from enum import Enum
#import telegram

#from wrapt_timeout_decorator import *

LOGIN_TEMPLATE = b'\xa0\x00\x00\x60%b\x00\x00\x00%b%b%b%b\x04\x01\x00\x00\x00\x00\xa1\xaa%b&&%b\x00Random:%b\r\n\r\n'
GET_SERIAL = b'\xa4\x00\x00\x00\x00\x00\x00\x00\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
               b'\x00\x00\x00\x00\x00\x00\x00'
GET_CHANNELS = b'\xa8\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
               b'\x00\x00\x00\x00\x00\x00\x00\x00'
GET_PTZ = b'\xa4\x00\x00\x00\x00\x00\x00\x00\x0b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
               b'\x00\x00\x00\x00\x00\x00\x00\x00'
GET_SOUND = b'\xa4\x00\x00\x00\x00\x00\x00\x00\x1a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
               b'\x00\x00\x00\x00\x00\x00\x00\x00'
GET_SNAPSHOT = b'\x11\x00\x00\x00(\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
               b'\x00\x00\x00\n\x00\x00\x00%b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
               b'\x00\x00%b\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
JPEG_GARBAGE1 = b'\x0a%b\x00\x00\x0a\x00\x00\x00'
JPEG_GARBAGE2 = b'\xbc\x00\x00\x00\x00\x80\x00\x00%b'

# Ускорение / Perfomance
TIMEOUT = 11

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')

class Status(Enum):
    SUCCESS = 0
    BLOCKED = 2
    NONE = -1

class DahuaController:
    def __init__(self, ip=None, port=None):
        self.model = ''
        self.ip = ip
        self.port = port
        self.login = None
        self.password = None
        self.channels_count = -1
        self.status = Status.NONE

        self._socket = None
        

    def auth(self, login, password):
        self._socket = socket.create_connection((self.ip, self.port), TIMEOUT)
        self._socket.send(LOGIN_TEMPLATE % (struct.pack('b', 24 + len(login) + len(password)), login.encode('ascii'),
                                           (8 - len(login)) * b'\x00', password.encode('ascii'),
                                           (8 - len(password)) * b'\x00', login.encode('ascii'),
                                           password.encode('ascii'), str(int(time.time())).encode('ascii')))
        data = self._socket.recv(128)
        if len(data) >= 10:
            if data[8] == 1 and data[9] == 4:
                self.status = Status.BLOCKED
            elif data[8] == 0:
                self.login = login
                self.password = password
                self.status = Status.SUCCESS
            else:
                self.status = Status.NONE

        if self.status is Status.SUCCESS:
            self._socket.send(GET_PTZ)
            self.model = self.receive_msg().split(b'\x00')[0].decode('ascii')

            self.get_sound_info()
            self.get_ptz_info()
            self.get_channels_count()

    def get_sound_info(self):
        self._socket.send(GET_SOUND)
        get_soundInfo = self.receive_msg()
        self.sound = get_soundInfo.split(b'\x00')[0].decode('ascii')
#        bot = telegram.Bot(token="", request=telegram.utils.request.Request(connect_timeout=20, read_timeout=20))
#        chat_id = bot.get_updates()[-1].message.chat_id
#        bot.send_message(chat_id='635172118', text=self.model + "   :  " + self.sound, timeout=120)
        return self.sound

    def get_ptz_info(self):
        succ = '-PTZ-Sound-Mic'
        ptz_data = {
'DH-SD42212T-HN', 'CCTV-Camera-DH-SD50230U-HN', 'CCTV-Camera-DH-SD59220T-HN', 'DH-SD59220T-HN', 'CP-UNC-CS10L1W', 'DHI-HCVR4104C-S3', 'DHI-HCVR4104HS-S2', 'DHI-HCVR4108HS-S2', 'DHI-iDVR5116H-F', 'DHI-NVR4104H', 'DHI-NVR4104HS-P-4KS2', 'DHI-NVR4104-P', 'DHI-NVR4104_P', 'DHI-NVR4104-P-4KS2', 'DHI-NVR4104_W', 'DH-IPC-A35N', 'DH-IPC-A46P', 'DH-IPC-AW12W', 'DH-IPC-AW12WN', 'DH-IPC-AW12WP', 'DH-IPC-K15', 'DH-IPC-K15P', 'DH-IPC-KW12WP', 'DH-SD22204T-GN', 'DH-SD22204T-GN-W', 'DH-SD22204TN-GN', 'DH-SD29204T-GN-W', 'DH-SD-32D203S-HN', 'DH-SD42212T-HN', 'DH-SD42212TN-HN', 'DH-SD50120S-HN', 'DH-SD50220T-HN', 'DH-SD59120T-HN', 'DH-SD59120TN-HN', 'DH-SD59131UN-HNI', 'DH-SD59220SN-HN', 'DH-SD59220T-HN', 'DH-SD59220TN-HN', 'DH-SD59225U-HNI', 'DH-SD59230S-HN', 'DH-SD59230T-HN', 'DH-SD59230U-HNI', 'DH-SD59430U-HN', 'DH-SD59430U-HNI', 'DH-SD6582A-HN', 'DH-SD6C120T-HN', 'DH-SD-6C1220S-HN', 'DH-SD6C220S-HN', 'DH-SD6C220T-HN', 'DH-SD6C230S-HN', 'DVR-HF-A', 'IP2M-841B', 'IP2M-841B-UK', 'IP2M-841W-UK', 'IPC-A15', 'IPC-A35', 'IPC-A7', 'IP Camera', 'IPC-AW12W', 'IPC-HDBW1000E-W', 'IP', 'PTZ', 'IPC', 'IPC-HDBW1320E-W', 'IPC-HDPW4200F-WPT', 'IPC-HDPW4221F-W', 'IPC-HFW1000S-W', 'IPC-HFW1320S-W', 'IPC-HFW1435S-W', 'IPC-HFW2325S-W', 'IPC-HFW4431E-S', 'IPC-HFW5200E-Z12', 'IPC-K100W', 'IPC-K15', 'IPC-K200W', 'IPC-KW100W', 'IPC-KW10W', 'IPC-KW12W', 'IPD-IZ22204T-GN', 'IPM-721S', 'IP PTZ Dome', 'PTZ Dome', 'IPPTZ-EL2L12X-MINI-I', 'LTV-ISDNI3-SDM2', 'MDVR_MEUED', 'RVi-IPC11W', 'SD59120T-HN', 'SD59220TN-HN', 'SD6982A-HN', 'SDQCN8029Z', 'ST-712-IP-PRO-D', 'VTO2111D', 'XS-IPCV026-3W'}
        test_sound = re.findall('Dahua.Device.Record.General', self.sound)
#        self._socket.send(GET_PTZ)
#        get_ptzInfo = self.receive_msg()
#        self.model = get_ptzInfo.split(b'\x00')[0].decode('ascii')
        if self.model in ptz_data:
           self.model = self.model + succ
           return self.model
        elif test_sound:
           #print(test_sound) DEBUG
           self.model = self.model + "-Sound-Mic"
           return self.model
        else:
            self.model = "unknown"
            return self.model

    def get_channels_count(self):
        self._socket.send(GET_CHANNELS)
        channels = self.receive_msg()
        self.channels_count = channels.count(b'&&') + 1
        return self.channels_count

    def receive_msg(self):
        header = self._socket.recv(32)
        try:
            length = struct.unpack('<H', header[4:6])[0]
        except struct.error:
            raise struct.error
        data = self._socket.recv(length)
        return data

#    @timeout(15) # (wrapt_timeout_decorator) TODO: play with timer
    def get_snapshot(self, channel_id):
        channel_id = struct.pack('B', channel_id)
        self._socket.send(GET_SNAPSHOT % (channel_id, channel_id))
        self._socket.settimeout(4)
        data = self.receive_msg_2(channel_id)
        self._socket.settimeout(TIMEOUT)
        return data

    def receive_msg_2(self, c_id):
        garbage = JPEG_GARBAGE1 % c_id
        garbage2 = JPEG_GARBAGE2 % c_id
        data = b''
        i = 0
        while True: # i != 30
            buf = self._socket.recv(1460)
            if i == 0:
                buf = buf[32:]
            data += buf
            if b'\xff\xd9' in data:
                break
            i += 1
        while garbage in data:
            t_start = data.find(garbage)
            t_end = t_start + len(garbage)
            t_start -= 24
            trash = data[t_start:t_end]
            data = data.replace(trash, b'')
        while garbage2 in data:
            t_start = data.find(garbage2)
            t_end = t_start + 32
            trash = data[t_start:t_end]
            data = data.replace(trash, b'')
        return data

