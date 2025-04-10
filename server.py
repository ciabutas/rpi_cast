#!/usr/bin/env python3

import logging
import os
import sys
import json
from pathlib import Path
from bottle import Bottle, response
import socket

# Configure logging with rotation
log_file = 'RaspberryCast.log'
max_bytes = 10 * 1024 * 1024  # 10MB
backup_count = 3

handler = logging.handlers.RotatingFileHandler(
    log_file, maxBytes=max_bytes, backupCount=backup_count
)

logging.basicConfig(
    handlers=[handler],
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.DEBUG
)

# Add health check endpoint
@app.route('/health')
def health_check():
    return {"status": "healthy", "version": "3.0"}

# Add error handling
@app.error(500)
def error_handler(error):
    logger.error(f"Internal error: {error}")
    response.content_type = 'application/json'
    return json.dumps({'error': str(error)})

# Check if port is available
def check_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('localhost', port))
        sock.close()
        return True
    except:
        logger.error(f"Port {port} is already in use")
        return False

# Current configuration handling is scattered
DEFAULT_CONFIG = {
    "slow_mode": False,
    "new_log": True,
    "pi_hostname": "raspberrypi",
    "width": "",
    "height": "",
    "subtitle_search": False,
    "port": 2020
}

# Should create a proper config manager:
class ConfigManager:
    def __init__(self, config_file='rpi_cast.conf'):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        try:
            with open(self.config_file) as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except (IOError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load config: {e}")
            return DEFAULT_CONFIG.copy()

    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save config: {e}")

if len(sys.argv) > 1:
    config_file = sys.argv[1]
else:
    config_file = 'raspberrycast.conf'
config = load_config(config_file)

# Creating handler to print messages on stdout
root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

try:
    os.mkfifo("/tmp/cmd")
except OSError as e:
    # 17 means the file already exists.
    if e.errno != 17:
        raise

if config["new_log"]:
    os.system("sudo fbi -T 1 --noverbose -a  images/ready.jpg")

setState("0")
open('video.queue', 'w').close()  # Reset queue
logger.info('Server successfully started!')

app = Bottle()

SimpleTemplate.defaults["get_url"] = app.get_url


@app.hook('after_request')
def enable_cors():
    response.headers['Access-Control-Allow-Origin'] = '*'


@app.route('/static/<filename>', name='static')
def server_static(filename):
    return static_file(filename, root='static')


@app.route('/')
@app.route('/remote')
def remote():
    logger.debug('Remote page requested.')
    return template('remote')


@app.route('/stream')
def stream():
    url = request.query['url']  # Missing validation
    # Should add:
    if not url or not isinstance(url, str):
        return json.dumps({'error': 'Invalid URL'}), 400

    logger.debug('Received URL to cast: '+url)

    if 'slow' in request.query:
        if request.query['slow'] in ["True", "true"]:
            config["slow_mode"] = True
        else:
            config["slow_mode"] = False
        # TODO: Do we really want to write this to disk?
        with open(config_file, 'w') as f:
            json.dump(config, f)

    try:
        if ('localhost' in url) or ('127.0.0.1' in url):
            ip = request.environ['REMOTE_ADDR']
            logger.debug('''URL contains localhost adress. \
Replacing with remote ip : ''' + ip)
            url = url.replace('localhost', ip).replace('127.0.0.1', ip)

        if 'subtitles' in request.query:
            subtitles = request.query['subtitles']

            if ('localhost' in subtitles) or ('127.0.0.1' in subtitles):
                            ip = request.environ['REMOTE_ADDR']
                            logger.debug(
                                '''Subtitle path contains localhost adress.
Replacing with remote IP.''')
                            subtitles = subtitles\
                                .replace('localhost', ip)\
                                .replace('127.0.0.1', ip)

            logger.debug('Subtitles link is '+subtitles)
            urlretrieve(subtitles, "subtitle.srt")
            launchvideo(url, config, sub=True)
        else:
            logger.debug('No subtitles for this stream')
            if (
                    ("youtu" in url and "list=" in url) or
                    ("soundcloud" in url and "/sets/" in url)):
                playlist(url, True, config)
            else:
                launchvideo(url, config, sub=False)
            return "1"
    except Exception as e:
        logger.error(
            'Error in launchvideo function or during downlading the subtitles')
        logger.exception(e)
        return "0"


@app.route('/queue')
def queue():
    url = request.query['url']

    if 'slow' in request.query:
        if request.query['slow'] in ["True", "true"]:
            config["slow_mode"] = True
        else:
            config["slow_mode"] = False
        with open('raspberrycast.conf', 'w') as f:
            json.dump(config, f)

    try:
        if getState() != "0":
            logger.info('Adding URL to queue: '+url)
            if (
                    ("youtu" in url and "list=" in url) or
                    ("soundcloud" in url and "/sets/" in url)):
                playlist(url, False, config)
            else:
                queuevideo(url, config)
            return "2"
        else:
            logger.info('No video currently playing, playing url : '+url)
            if (
                    ("youtu" in url and "list=" in url) or
                    ("soundcloud" in url and "/sets/" in url)):
                playlist(url, True, config)
            else:
                launchvideo(url, config, sub=False)
            return "1"
    except Exception as e:
        logger.error('Error in launchvideo or queuevideo function !')
        logger.exception(e)
        return "0"


@app.route('/video')
def video():
    control = request.query['control']
    if control == "pause":
        logger.info('Command : pause')
        os.system("echo -n p > /tmp/cmd &")
        return "1"
    elif control in ["stop", "next"]:
        logger.info('Command : stop video')
        os.system("echo -n q > /tmp/cmd &")
        return "1"
    elif control == "right":
        logger.info('Command : forward')
        os.system("echo -n $'\x1b\x5b\x43' > /tmp/cmd &")
        return "1"
    elif control == "left":
        logger.info('Command : backward')
        os.system("echo -n $'\x1b\x5b\x44' > /tmp/cmd &")
        return "1"
    elif control == "longright":
        logger.info('Command : long forward')
        os.system("echo -n $'\x1b\x5b\x41' > /tmp/cmd &")
        return "1"
    elif control == "longleft":
        logger.info('Command : long backward')
        os.system("echo -n $'\x1b\x5b\x42' > /tmp/cmd &")
        return "1"


@app.route('/sound')
def sound():
    vol = request.query['vol']
    if vol == "more":
        logger.info('REMOTE: Command : Sound ++')
        os.system("echo -n + > /tmp/cmd &")
    elif vol == "less":
        logger.info('REMOTE: Command : Sound --')
        os.system("echo -n - > /tmp/cmd &")
    setVolume(vol)
    return "1"


@app.route('/shutdown')
def shutdown():
    time = request.query['time']
    if time == "cancel":
        os.system("shutdown -c")
        logger.info("Shutdown canceled.")
        return "1"
    else:
        try:
            time = int(time)
            if (time < 400 and time >= 0):
                shutdown_command = "shutdown -h +" + str(time) + " &"
                os.system(shutdown_command)
                logger.info("Shutdown should be successfully programmed")
                return "1"
        except:
            logger.error("Error in shutdown command parameter")
            return "0"


@app.route('/running')
def webstate():
    currentState = getState()
    logger.debug("Running state as been asked : "+currentState)
    return currentState

@app.route('/health/youtube')
def youtube_health_check():
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Test video
    try:
        result = return_full_url(test_url, sub=False, slow_mode=False)
        if result:
            return "YouTube extraction working"
        return "YouTube extraction failed", 500
    except Exception as e:
        logger.error(f"YouTube health check failed: {str(e)}")
        return f"YouTube health check failed: {str(e)}", 500

debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
port = int(os.environ.get('PORT', 2020))
run(app, reloader=False, host='0.0.0.0', debug=debug_mode, quiet=True, port=port)
