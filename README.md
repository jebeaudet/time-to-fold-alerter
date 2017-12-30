# Time to fold alerter
A little rough script to detect a washing machine/dryer load and alert you with [Telegram](https://telegram.org/) or any other GET webhook when the load is over. Useful when you don't hear the end of cycle sound. It uses the ADXL345 accelerometer with this [convenient driver](https://github.com/pimoroni/adxl345-python) for raspberry pi.

# How to use
Make sure you have a functional setup with the ADXL345 and that the sensor is anchored on the machine, ready to measure on the **Z** axis.

All the steps mentioned here should be executed on the raspberry pi.
## Install the driver
1. Clone the [repository](https://github.com/pimoroni/adxl345-python)
2. Add the driver path to your `PYTHONPATH` environment variable (`export PYTHONPATH=$PYTHONPATH:/somedirectory/adxl345-python`)

## Install the script
1. Clone the [repository](https://github.com/jebeaudet/time-to-fold-alerter)
2. Run with `python time_to_fold_alerter.py https://api.telegram.org/botxxxx/sendMessage?chat_id=xxxxxx&text=Done`

## Optional configuration
On the first run, you can run with the `-v` flag and this will output relevant information in the log file (`/var/log/time_to_fold_alerter.py`) such as the maximum acceleration detected in the idle phase detection. You can also configure the idle threshold that is used to detect movement with the `-i` flag.

Help is also available with `python time_to_fold_alerter.py -h` : 
```
$ python time_to_fold_alerter.py -h
usage: time_to_fold_alerter.py [-h] [-v] [-i IDLE_THRESHOLD] [-a ADDRESS] notification_url

Washing machine/dryer action detector. Logs are in
/var/log/time_to_fold_alerter.log.

positional arguments:
  notification_url      the url to send the notification to via a GET

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         run the program with debug logs
  -i IDLE_THRESHOLD, --idle_threshold IDLE_THRESHOLD
                        the idle threshold for movement detection (default:
                        0.1)
  -a ADDRESS, --address ADDRESS
                        the address of the adxl354 in int or hexadecimal,
                        useful when you use multiple sensors on the same board
                        (default: 0x53)
```

# How does it work?
The script uses a very simple state machine since the pi is not really suitable for complex live FFT calculations. It uses the following algorithm : 
- poll the sensor for 1 second each 10 seconds
- if output is higher than the configurable `idle_threshold`, increment a counter and repeat
- if counter > 2, it means we have a load
- loop until the maximum acceleration is below the `idle_threshold` for 1 minute straight.
- send notification

While the flow is not very elaborated, it's very reliable in my experience but might requires tuning for other machines as I've only tested with one.

# Questions or issues?
Open an issue!