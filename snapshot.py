# -*- coding:utf-8 -*-

import threading
import logging
import sys
import io
import os

from time import sleep
from PIL import Image
import numpy as np
from cv2 import cvtColor, Canny
from cv2 import COLOR_BGR2GRAY, bilateralFilter

from paint import *
import config


class ScreenshotThread(threading.Thread):
    def __init__(self, screenshot_queue, image_processing_queue):
        threading.Thread.__init__(self)
        self.screenshot_queue = screenshot_queue
        self.image_processing_queue = image_processing_queue

    def run(self):
        while True:
            with threading.Lock():
                dahua = self.screenshot_queue.get()
            if config.snapshots_enabled:
                self.make_snapshots(dahua)
            self.screenshot_queue.task_done()

    def make_snapshots(self, dahua):
        model = dahua.model
        channels_count = dahua.channels_count
        logging.debug(f' Make snapshot from {dahua.ip} (DM: {dahua.model}, channels: {channels_count})')
        config.trash_cam[dahua.ip] = 0
        dead_counter = 0
        capturing = 0
        total_channels = config.ch_count
        for channel in range(channels_count):
            # Ускорение / Performance
            if dead_counter > 4 or config.trash_cam[dahua.ip] > 2:
                logging.debug(f' {dead_counter} dead channels in a row. Skipping this cam')
                break
            try:
                jpeg = dahua.get_snapshot(channel)
                dead_counter = 0
                capturing += 1
                name = f"{dahua.ip}_{dahua.port}_{dahua.login}_{dahua.password}_{channel + 1}_{model}.jpg"
                grabster = channels_count - capturing
                print(fore_green(f"Brute progress: [{config.state}] Grabbing snapshots for {dahua.ip}.. \n")  # Left {str(grabster)} channels.. Trash: {str(config.trash_cam[dahua.ip])}\n")
                + back_yellow(f"Writing snapshots.. Total saved {config.snapshots_counts} from {total_channels}"), end='\r')
                sleep(0.05)
                self.image_processing_queue.put([name, jpeg], block=False, timeout=20)
                # self.image_processing(jpeg)
            except Exception as e:
                logging.debug(f' Channel {channel + 1} of {dahua.ip} is dead {str(e)}{" "*40}')
                dead_counter += 1
                continue
        logging.debug("%s exit from make_snapshots()" % dahua.ip)
        return


class ImageProcessingThread(threading.Thread):
    def __init__(self, image_processing_queue):
        threading.Thread.__init__(self)
        self.image_processing_queue = image_processing_queue

    def run(self):
        while True:
            with threading.Lock():
                # print(self.image_processing_queue.get())
                name, image = self.image_processing_queue.get()
            self.processing(name, image)
            self.image_processing_queue.task_done()

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

    def processing(self, name, image_bytes):
        n_name = name.split("_")
        n_ip = n_name[0]
        try:
            pil_image = Image.open(io.BytesIO(image_bytes))
            image = np.array(pil_image)
            if self.is_dark(image) or not self.is_interesting(image):
                self.save_image(os.path.join('trash', name), image_bytes)
                config.trash_cam[n_ip] += 1
                return False
            else:
                self.save_image(name, image_bytes)
                config.trash_cam[n_ip] = 0
                return True
        except Exception as e:
            config.trash_cam[n_ip] += 1
            #print("PIL Issue: " + str(e))
            logging.debug(f'{fore_red("Cannot save screenshot")} - {name.split("_")[0]} - {back_red("CORRUPTED FILE")}{" "*40}')
            pass

    def save_image(self, name, image_bytes):
        n_name = name.split("_")
        n_ip = n_name[0]
        try:
            with open(os.path.join(config.snapshots_folder, name), 'wb') as outfile:
                outfile.write(image_bytes)
            config.snapshots_counts += 1
            logging.debug(f' {fore_green(f"Saved snapshot - {name}")}{" "*40}')
        except Exception as e:
            config.trash_cam[n_ip] += 1
            #print(" Outfile: " + e)
            logging.debug(f'{fore_red("Cannot save screenshot")} - {name}{" "*40}')
