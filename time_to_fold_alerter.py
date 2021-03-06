#!/usr/bin/env python

from adxl345 import ADXL345
import time
import urllib2
import math
import logging
import argparse
import signal
import sys

class SignalHandler():
    running = True
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.running = False

def auto_int(x):
    return int(x, 0)

def get_maximum_acceleration_on_sample(duration_in_seconds):
    accelerations = []
    now = time.time()
    while((time.time() - now) < duration_in_seconds):
        try:
            axes = sensor.getAxes(True)
            accelerations.append(math.fabs(axes['z']))
            time.sleep(0.01)
        except IOError:
            logger.exception("Error while sampling from the ADXL354, ignoring")
    return max(accelerations)

def validate_movement(number_of_period, sampling_period, idle_threshold):
    accelerations = []
    for i in range(0, number_of_period):
        accelerations.append(get_maximum_acceleration_on_sample(sampling_period))
    max_acceleration = max(accelerations)
    logger.debug("Maximum acceleration of '%s' detected for movement detection", max_acceleration)
    return max_acceleration > idle_threshold


parser = argparse.ArgumentParser(description="Washing machine/dryer action detector. Logs are in /var/log/time_to_fold_alerter.log.")
parser.add_argument(dest="notification_urls", nargs='+',
                   help="the url(s) to send the notification to via a GET")
parser.add_argument("-v", "--verbose", action="store_true", help="run the program with debug logs")
parser.add_argument("-i", "--idle_threshold", dest="idle_threshold", type=float, default=0.1,
                   help="the idle threshold for movement detection (default: %(default)s)")
parser.add_argument("-a", "--address", dest="address", type=auto_int, default=0x53,
                   help="the address of the adxl354 in int or hexadecimal, useful when you use multiple sensors on the same board (default: 0x53)")
args = parser.parse_args()

sensor = ADXL345(args.address)
#sensor = ADXL345(0x1d)

logging.basicConfig(filename="/var/log/time_to_fold_alerter.log", level=logging.DEBUG if args.verbose else logging.INFO, format="%(asctime)-15s %(message)s")
logger = logging.getLogger("time_to_fold_alerter")

working = False
consecutive_counter=0
idle_threshold = args.idle_threshold
notification_urls = args.notification_urls

logger.info("Alerter launched, monitoring for movement now. Idle threshold : %s. ADXL address : %s. Verbose log : %s. Notication urls : %s.", idle_threshold, args.address, args.verbose, notification_urls)
signal_handler = SignalHandler()
while(signal_handler.running):
    try:
        if not working:
            acceleration = get_maximum_acceleration_on_sample(1)
            logger.debug("Maximum acceleration of '%s' detected for idle detection", acceleration)
            if(acceleration < idle_threshold):
                if(consecutive_counter != 0):
                    logger.info("False positive for movement, reseting the consecutive movement counter to 0")
                else:
                    logger.debug("No movement detected, sleeping for 10 seconds")
                time.sleep(10)
                consecutive_counter = 0;
            else:
                consecutive_counter += 1
                logger.info("Movement possibly detected, incrementing the movement counter to '%s'", consecutive_counter)
                time.sleep(1)

            if (consecutive_counter == 3):
                logger.info("We have a washing machine/dryer load!")
                working = True
                consecutive_counter = 0
        else:
            while(validate_movement(60, 1, idle_threshold)):
                if not signal_handler.running:
                    break
                logger.debug("Still working!")
                time.sleep(1)

            logger.info("All done, sending notifications!")
            for notification_url in notification_urls:
                try:
                    logger.info("Sending notification to '%s'", notification_url)
                    urllib2.urlopen(notification_url)
                except:
                    logger.exception("Error while sending notification!")

            working = False
    except:
        logger.exception("Oops something went terribly wrong!")

logger.info("Caught SIGTERM or SIGINT, exiting.")
sys.exit(0)
