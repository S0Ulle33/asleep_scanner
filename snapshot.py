# -*- coding:utf-8 -*-
import threading
import queue
import logging
import sys
import io
from pathlib import PurePath

from time import sleep
from PIL import Image
import numpy as np
from cv2 import cvtColor, Canny
from cv2 import COLOR_BGR2GRAY, bilateralFilter

from paint import *
import config

class ScreenshotThread(threading.Thread):
    def __init__(self, screenshot_queue):
        threading.Thread.__init__(self)

        self.screenshot_queue = screenshot_queue
        self.trash_counter = 0

    def run(self):
        while True:
            with threading.Lock():
                dahua = self.screenshot_queue.get()
            if config.snapshots_enabled:
                self.make_snapshots(dahua)
            self.screenshot_queue.task_done()

    def make_snapshots(self, dahua):
        logging.debug(f'Make snapshot from {dahua.ip} (DM: {dahua.model}, channels: {dahua.channels_count})')
        self.trash_counter = 0
        dead_counter = 0
        total_channels = config.ch_count

        for channel in range(dahua.channels_count):
            if dead_counter > 4:
                logging.debug(f'{dead_counter} dead channels in a row. Skipping this cam')
                break
            if self.trash_counter > 2:
                logging.debug(f'{self.trash_counter} trash channels in a row. Skipping this cam')
                break
                
            try:
                snapshot = dahua.get_snapshot(channel)
            except Exception as e:
                logging.debug(f'Channel {channel + 1} of {dahua.ip} is dead: {str(e)}')
                dead_counter += 1
                continue
            dead_counter = 0
            
            print(fore_green(f'Brute progress: [{config.state}] Grabbing snapshots for {dahua.ip}.. \n')
                + back_yellow(f'Writing snapshots.. Total saved {config.snapshots_counts} from {total_channels}'), end='\r')
            sleep(0.05)

            name = f"{dahua.ip}_{dahua.port}_{dahua.login}_{dahua.password}_{channel + 1}_{dahua.model}.jpg"
            try:
                if self.is_trash(snapshot):
                    self.trash_counter += 1
                    self.save_image(PurePath('trash', name), snapshot)
                else:
                    self.trash_counter = 0
                    self.save_image(name, snapshot)
            except Exception as e:
                logging.debug(f'{fore_red(f"Cannot open snapshot: {str(e)}")}')
            
        logging.debug(f'{dahua.ip} exit from make_snapshots()')

    def is_trash(self, snapshot):
        pil_image = Image.open(io.BytesIO(snapshot))
        image = np.array(pil_image)
        return self.is_dark(image) and not self.is_interesting(image)

    def is_dark(self, image):
        x = np.sum(image)/image.size
        if x < 50:
            return True
        else:
            return False

    def is_interesting(self, image):
        gray = cvtColor(image, COLOR_BGR2GRAY)
        gray = bilateralFilter(gray, 11, 17, 17)
        edged = Canny(gray, 30, 200)
        if np.sum(edged[:, :]**2) < 2500:
            return False
        else:
            return True

    def save_image(self, name, image_bytes):
        try:
            with open(PurePath(config.snapshots_folder, name), 'wb') as outfile:
                outfile.write(image_bytes)
            config.snapshots_counts += 1
            logging.debug(f'{fore_green(f"Saved snapshot - {name}")}')
        except Exception as e:
            self.trash_counter += 1
            logging.debug(f'{fore_red(f"Cannot save snapshot - {name}:")} {back_red(f"{str(e)}")}')
