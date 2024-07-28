#!/bin/python3

from datetime import datetime
from io import BytesIO
from libcamera import Transform
from picamera2 import Picamera2

# Includes from this project.
from includes.image import ImageProcessor


class Camera:
    """
    Class used to manage camera.

    Attributes:
        _picam2 (Picamera2): Picamera2 object.
        _configuration_preview (dict): Config in preview mode.
        _configuration_still (dict): Config in capture mode.
    """


    def __init__(self, preview_width, preview_height):
        """
        Init camera and its configuration.

        Args:
            preview_width (int): width (px) for preview image.
            preview_height (int): height (px) for preview image.
        """

        # Init Picamera2 object.
        self._picam2 = Picamera2()

        # Init preview and capture configurations.
        self._configuration_preview = {"format": "RGB888",
                                       "size": (preview_width, preview_height)}
        self._configuration_still = {"format": "RGB888"}


    def initialize_camera(self, preview_mode, reduce_size = False):
        """
        Init camera and its configuration.

        Args:
            preview_mode (bool): Go in preview or capture mode.
                            True if switching to preview mode.
                            False if switching to capture mode.
            reduce_size (bool): Request a lower size.
        """

        # Get attributes.
        picam2 = self._picam2
        preview = self._configuration_preview
        still = self._configuration_still
    
        # Stop before switch camera mode.
        picam2.stop()

        # Mode preview or still (capture).
        if preview_mode:
            mirror = Transform(hflip = True)
            picam2.configure(picam2.create_preview_configuration(main=preview, transform=mirror))
        else:
            # Get max resolution.
            size = picam2.sensor_modes[3]['size']

            # If image requested with lower resolution.
            if reduce_size:
                size = (size[0]//3, size[1]//3)
            
            # Create Dict with size to merge with still configuration. 
            requested_size = {'size': size}

            picam2.configure(picam2.create_still_configuration(main=still | requested_size))

        # (Re)start camera.
        picam2.start()


    def close_camera(self):
        """
        Stop camera to avoid busy device.
        """

        self._picam2.stop()


    def generate_video(self, background):
        """
        Generate video stream from camera.

        Args:
            background (str):
        """

        # Get attributes.
        picam2 = self._picam2

        # Generate jpeg image continuously.
        while True:
            stream = BytesIO()
            picam2.capture_file(stream, format='jpeg')

            # Change background if requested.
            if background != 'nobackground':

                # Create ImageProcessor object to edit image.
                processor = ImageProcessor(stream)

                # Send background instructions.
                processor.background(background, False)

                # Commit all pending operations.
                processor.commit()

            stream.seek(0)
            yield(b'--frame\r\n'
                  b'Content-Type: image/jpeg\r\n\r\n' + stream.read() + b'\r\n')


    def capture_img(self, filename, background, add_date, add_time, add_text, font = ''):
        """
        Capture image in full resolution from camera.

        Args:
            filename (str): Name of image file to save.
            background (str): Name of background image file.
            add_date (bool): Write current date on captured image.
            add_time (bool): Write current time on captured image.
            add_text (string): Write text message on captured image.
            font (string, optional): Font familly used on text message.

        Returns:
            str or None: Error message or None if success.
        """

        try:

            # Image edition requested.
            if background != 'nobackground' or add_text != '' \
                    or add_date == True or add_time == True:
                edit_requested = True
            else:
                edit_requested = False

            # Switch camera to still mode.
            self.initialize_camera(False, edit_requested)

            # Take image in PNG format.
            stream = BytesIO()
            self._picam2.capture_file(stream, format='png')

            # Switch camera to preview mode.
            self.initialize_camera(True)

            # Image edition requested.
            if edit_requested:

                # Create ImageProcessor object to edit image.
                processor = ImageProcessor(stream)

                # Add background on image.
                if background != 'nobackground':
                    # Send background instructions.
                    processor.background(background)

                # Add text on image.
                if add_text != '':

                    # Default font familly.
                    if font == '':
                        processor.add_text(add_text, (0, 30),
                                        'center_bottom', font_size=75)

                    # Optional custom font selected.
                    else:
                        processor.add_text(add_text, (0, 30), 'center_bottom',
                                           font_size=75, font_familly=font)

                # Add current date on image.
                if add_date == True:
                    date = datetime.now().strftime("%d/%m/%Y")
                    processor.add_text(date, (20, 20), 'top_right')

                # Add current time on image.
                if add_time == True:
                    time = datetime.now().strftime("%H:%M:%S     ")
                    processor.add_text(time, (20, 70), 'top_right')

                # Commit all pending operations.
                processor.commit()

            # Save image to disk.
            with open(filename, 'wb') as f:
                f.write(stream.getvalue())

            print(f"Image saved at {filename}")

        except Exception as e:
            print(f"Error capturing image: {e}")
            return "Error capturing image"

        return None
