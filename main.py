#!/bin/python3
#
# Pi-Photobooth  Copyright (C) 2024  Corentin SORIANO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import os
import signal
import sys
import threading
from datetime import datetime
from flask import Flask, jsonify, render_template, Response, url_for, send_from_directory, send_file, abort, request
from gpiozero import CPUTemperature

# Includes from this project.
from includes.camera import Camera
from includes.config import ConfigFile
from includes.gpio import ManageGPIO
from includes.language import Language
from includes.misc import str_to_bool, generate_qrcode
from includes.print import Printer
from includes.webdav import WebDAVSync


# Init various objects.
app = Flask(__name__)
config = ConfigFile()

# Init lang translations.
lang = Language(config.get('main', 'lang'))

# Init camera.
camera = Camera(int(config.get('camera', 'width')), 
                int(config.get('camera', 'height')))

# Override cups host if requested in config file.
if config.get('cups', 'host') != '':
    os.environ['CUPS_SERVER'] = config.get('cups', 'host')

# Override cups port if requested in config file.
if config.get('cups', 'port') != '':
    os.environ['CUPS_PORT'] = config.get('cups', 'port')

# Init printer.
printer = Printer(config.get('cups', 'printer'))

# Get GPIO configuration and init ManageGPIO object.
GPIO_LEGACY = str_to_bool(config.get('gpio', 'legacy_mode'))
GPIO_ADMIN_BTN = int(config.get('gpio', 'admin_button'))
gpio = ManageGPIO(GPIO_LEGACY)

# Init webdav object if enabled feature.
if str_to_bool(config.get('dav', 'enabled')):
    webdav = WebDAVSync(config.get('dav', 'endpoint'),
                        config.get('dav', 'username'),
                        config.get('dav', 'password'))
else:
    webdav = None


def handle_exit(*args):
    """
    Handle the graceful exit of the application by closing the camera.
    This function is intended to be used as a signal handler for codes
    SIGINT (Ctrl+C) or SIGTERM.

    Args:
        *args: Variable length argument list. This is typically used to
               pass signal number and frame information when the function
               is used as a signal handler.

    Raises:
        SystemExit: This function will terminate the program by raising
                    SystemExit with a status code of 0.
    """

    # Send stop event to threads.
    stop_event.set()

    # Close camera before exit.
    camera.close_camera()

    # Close GPIO PINs.
    if GPIO_LEGACY:
        gpio.cleanup()
    else:
        gpio_pins = [
            GPIO_ADMIN_BTN,
        ]
        gpio.cleanup(gpio_pins)
    
    # Wait for threads to terminate.
    if webdav:
        dav_thread.join()

    # Exit python application.
    sys.exit(0)


def check_ip_restrict(ip):
    """
    Check if client can access this url or not.

    Args:
        ip (string): IP address to check.
    """

    # Get boolean in config file.
    restrict_enabled = str_to_bool(config.get('main', 'ip_restrict'))

    # Loopback address.
    localhost = '127.0.0.1'

    if restrict_enabled and ip != localhost:
        # HTTP Forbiden
        abort(403)


@app.after_request
def add_headers(response):
    """
    Add headers like CSP to each requests to enhance security.

    This function is executed after each request is processed by Flask.
    It adds a Content-Security-Policy (CSP) header to the response.

    Args:
        response (Response): The response object to which headers are added.

    Returns:
        Response: The modified response object with added headers.
    """

    # Add CSP.
    response.headers['Content-Security-Policy'] = (
        "default-src 'none'; "
        "img-src 'self'; "
        "script-src 'self'; "
        "style-src 'self'; "
        "font-src 'self'; "
        "connect-src 'self'; "
    )

    return response


@app.route('/')
def index():
    """
    Renders and returns the index.html template when the root URL is accessed.

    Returns:
        str: The rendered HTML template for the homepage.
    """

    # Restricted enpoint.
    check_ip_restrict(request.remote_addr)

    return render_template('index.html', lang=lang)


@app.route('/video_feed/<path:background>')
def video_feed(background):
    """
    Stream video feed from the camera and optionaly add a background on image.

    Args:
        background (str): The path variable indicating whether to include a background. 
                          If 'nobackground', video is streamed without background.

    Returns:
        Response: The video stream response with the appropriate MIME type.
    """

    # Restricted enpoint.
    check_ip_restrict(request.remote_addr)

    # Check if green background is enabled.
    green_background = str_to_bool(config.get('main', 'green_background'))

    # Stream video.
    return Response(camera.generate_video(background, green_background),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/capture/<path:background>')
def capture(background):
    """
    Capture an image and save it with a timestamped filename.

    This route captures an image using the camera and saves it to the 'images' 
    directory with a filename based on the current timestamp. If the capture is
    successful, it returns the filename. If there is an error, it returns the
    error message.

    Returns:
        str: The filename of the captured image if successful.
        str: The error message if the capture fails.
    """

    # Restricted enpoint.
    check_ip_restrict(request.remote_addr)

    # Generate filename for new image.
    date = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    filename = f"images/photo_{date}.png"

    # Capture image.
    error = camera.capture_img(filename, background,
                               str_to_bool(config.get('main', 'green_background')),
                               str_to_bool(config.get('main', 'disable_ai_cut')),
                               str_to_bool(config.get('main', 'enable_date')),
                               str_to_bool(config.get('main', 'enable_time')),
                               config.get('main', 'message'),
                               config.get('main', 'message_font'))

    # Send error message to frontend.
    if error != None:
        return error

    # Backup picture to WebDAV server (async job).
    if webdav:
        webdav.add_operation('push', filename)

    # Send filename to frontend.
    return filename


@app.route('/print/<action>/<path:job>')
def print_file(action, job):
    """
    Launch print file and monitor printing job.

    Args:
        action (str): Requested action (start/monitoring/...).
        job (str): Filename or job id.

    Returns:
        Response: The response object containing json status.
    """

    # Print picture.
    if action == 'start':
        result = {
            "filename": job,
            "job_id": printer.print(job)
        }

    # Monitoring pending job.
    elif action == 'monitoring':
        result = {
            "job_id": job,
            "state": printer.monitor_job(job)
        }

    # Unknown endpoint.
    else:
        return '', 404

    # Return json with result.
    return jsonify(result)


@app.route('/js/<path:filename>')
def serve_js(filename):
    """
    Serve JavaScript files from the 'js' directory.

    When a request is made to '/js/<filename>', the file with the given filename
    is retrieved from the 'js' directory and served to the client.

    Args:
        filename (str): The name of the JavaScript file to be served.

    Returns:
        Response: The response object containing the requested JavaScript file.
    """

    # Restricted enpoint.
    check_ip_restrict(request.remote_addr)

    return send_from_directory('js', filename)


@app.route('/css/<path:filename>')
def serve_css(filename):
    """
    Serve CSS files from the 'templates/css' directory.

    When a request is made to '/css/<filename>', the file with the given filename
    is retrieved from the 'templates/css' directory and served to the client.

    Args:
        filename (str): The name of the CSS file to be served.

    Returns:
        Response: The response object containing the requested CSS file.
    """

    # Restricted enpoint.
    check_ip_restrict(request.remote_addr)

    return send_from_directory('templates/css', filename)


@app.route('/translations')
def get_translations():
    """
    Send json translations to frontend.

    Returns:
        Response: The response object containing json translations.
    """

    return jsonify(lang.readFile())


@app.route('/images/<path:filename>')
def serve_images(filename):
    """
    Serve images files from the 'images' directory.

    When a request is made to '/images/<filename>', the file with the given filename
    is retrieved from the 'images' directory and served to the client.

    Args:
        filename (str): The name of the image file to be served.

    Returns:
        Response: The response object containing the requested image file.
    """

    # Restricted enpoint.
    check_ip_restrict(request.remote_addr)

    return send_from_directory('images', filename)


@app.route('/background/<path:background>')
def serve_background(background):
    """
    Serve background images files from the 'background' directory.

    When a request is made to '/background/<filename>', the file with the given
    filename is retrieved from the 'background' directory and served to the client.

    Args:
        filename (str): The name of the background image file to be served.

    Returns:
        Response: The response object containing the requested background image file.
    """

    # Restricted enpoint.
    check_ip_restrict(request.remote_addr)

    backgrounds_dir = 'backgrounds'

    # Get background item list.
    if background == 'list':
        try:
            files = os.listdir(backgrounds_dir)
            image_files = [file for file in files if file.lower().endswith(('.jpg', '.jpeg', '.png'))]
            image_files.sort()
            return jsonify(image_files)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # Send background image.
    else:
        return send_from_directory(backgrounds_dir, background)


@app.route('/qrcode/<path:filename>')
def serve_qrcode(filename):
    """
    Serve qrcodes generated on-the-fly.

    When a request is made to '/qrcode/<filename>', a qrcode is generated using
    url from config file and filename parameter.

    Args:
        filename (str): The name of the image file to link to the qrcode.

    Returns:
        Response: The response object containing the qrcode.
    """

    # Restricted enpoint.
    check_ip_restrict(request.remote_addr)

    # Get full image url.
    platform_url = config.get('main', 'public_url')
    full_url = platform_url + filename

    # Generate and send qrcode.
    return send_file(generate_qrcode(full_url), mimetype='image/png')


@app.route('/gpio/<path:name>')
def gpio_state(name):
    """
    Returns the status of a specific gpio by pretty name.

    Args:
        name (str): Pretty name of a gpio.

    Returns:
        str: Json with state of the requested gpio.
             If requested gpio does not exist, returns a 404 http code.
    """

    # Restricted enpoint.
    check_ip_restrict(request.remote_addr)

    # Get requested GPIO number.
    gpio_number = config.get('gpio', name)

    # Is defined this PIN in config file ?
    if gpio_number == None:
        return '', 404

    # Cast to int.
    gpio_number = int(gpio_number)

    # Out of RPI bounds.
    if gpio_number < 1 or gpio_number > 40:
        return '', 404

    # Get state for requested gpio.
    gpio_state = gpio.get_state(gpio_number)

    # Return state for requested gpio.
    return jsonify({"state": gpio_state})


@app.route('/health')
def get_health():
    """
    Get system health (temperature, printer, ...).

    Returns:
        str: Current system health in json format.
    """

    # Restricted enpoint.
    check_ip_restrict(request)

    response = jsonify({
        "temp": CPUTemperature().temperature,
        "printer": printer.monitor_printer(),
    })

    return response


@app.route('/power/<path:action>')
def power(action):
    """
    Reboot or shutdown RPI.

    Args:
        action (str): Action requested (reboot or shutdown)

    Returns:
        str: state of request.
    """

    # Restricted enpoint.
    check_ip_restrict(request)

    if (action == 'reboot'):
        state = "Reboot requested."
        os.system('sudo reboot')

    elif (action == 'shutdown'):
        state = "Shutdown requested."
        os.system('sudo poweroff')

    else:
        state = "Error: unknown action."

    return jsonify({"state": state})


@app.route('/settings', methods=['GET', 'PUT'])
def handle_settings():
    """
    Handle settings updates from frontend.

    Returns:
        Json with new settings values.
    """

    # Update settings.
    if request.method == 'PUT':

        # Get json body content.
        green_background = request.json.get('green_background')
        disable_ai_cut = request.json.get('disable_ai_cut')
        enable_date = request.json.get('enable_date')
        enable_time = request.json.get('enable_time')
        message = request.json.get('message')

        if green_background != config.get('main', 'green_background'):
            if isinstance(green_background, bool):
                config.set('main', 'green_background', green_background)

        if disable_ai_cut != config.get('main', 'disable_ai_cut'):
            if isinstance(disable_ai_cut, bool):
                config.set('main', 'disable_ai_cut', disable_ai_cut)

        if enable_date != config.get('main', 'enable_date'):
            if isinstance(enable_date, bool):
                config.set('main', 'enable_date', enable_date)

        if enable_time != config.get('main', 'enable_time'):
            if isinstance(enable_time, bool):
                config.set('main', 'enable_time', enable_time)

        if message != config.get('main', 'message'):
            config.set('main', 'message', message)

    # Get settings.
    settings = {
        'green_background': config.get('main', 'green_background'),
        'disable_ai_cut': config.get('main', 'disable_ai_cut'),
        'enable_date': config.get('main', 'enable_date'),
        'enable_time': config.get('main', 'enable_time'),
        'message': config.get('main', 'message'),
    }

    # Send settings to client.
    return jsonify(settings)


def dav_sync_thread(stop_event):
    """
    Thread for dav sync.

    Args:
        stop_event (Event): Thread stop event.
    """

    while not stop_event.is_set():

        # Flush all requested operations.
        webdav.sync(stop_event)

        # Remove obsolete backgrounds and images.
        stop_event.wait(1)
        webdav.remove_obsolete('images')
        stop_event.wait(1)
        webdav.remove_obsolete('backgrounds')

        # Get remote backgrounds.
        stop_event.wait(1)
        webdav.pull_folder('backgrounds')

        # Wait before restart.
        stop_event.wait(1)


if __name__ == '__main__':

    # Init camera in preview mode.
    camera.initialize_camera(True)

    # Register signal handlers.
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    # Init GPIO PINs.
    gpio.setup_pin(GPIO_ADMIN_BTN)

    # Run async job in new thread for dav sync.
    if webdav:
        stop_event = threading.Event()
        dav_thread = threading.Thread(target=dav_sync_thread,
                                      args=(stop_event,))
        dav_thread.start()

    # Run flask server app.
    listen = config.get('main', 'listen')
    port = config.get('main', 'port')
    app.run(host=listen, port=port, debug=False)
