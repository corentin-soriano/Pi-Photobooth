#!/bin/python3

import cv2
import numpy
from PIL import Image, ImageDraw, ImageFont
from rembg import remove, new_session

# DEBUG :
from datetime import datetime


class ImageProcessor:
    """
    Class used to modify images.

    Attributes:
        _operations (list): with all requested operations.
        _image (ByteIO): Image to modify.
    """


    def __init__(self, image):
        """
        Init _operations and _image attributes.

        Args:
            image (ByteIO): PNG image to modify.
        """

        self._operations = []
        self._image = image


    def add_text(self, text, offset, from_edge, font_size=50,
                 font_familly='Quicksand-Medium.ttf', color=(255, 255, 255)):
        """
        Store requested text and parameters to write on commit.

        Args:
            text (str): Text to write.
            offset (tuple): Offset of position (x, y) based on from_edge and img/font size.
            from_edge (str): Position from this edge.
            font_size (int, optional): Font size, default = 20px.
            font_familly (str, optional): Font familly used.
            color (tuple, optional): RGB color of the text. Default = white.
        """

        # Dict with requested parameters for this text.
        text_params = {
            'type': 'add_text',
            'text': text,
            'offset': offset,
            'from_edge': from_edge,
            'font_size': font_size,
            'font_familly': font_familly,
            'color': color,
        }

        # Append params to pending operations.
        self._operations.append(text_params)


    def background(self, name, quality = True):
        """
        Store requested text and parameters to write on commit.

        Args:
            text (str): Name of background file to use.
            quality (bool, optional): Improve quality or speed.
        """

        # Dict with requested parameters for this text.
        background_params = {
            'type': 'background',
            'name': name,
            'quality': quality,
        }

        # Append params to pending operations.
        self._operations.append(background_params)


    def commit(self):
        """
        Commit all pending operations on image.

        Change background and next add text on image if requested.
        """

        # Get operations.
        operations = self._operations

        # Open image with PIL.
        img = Image.open(self._image).convert("RGBA")

        # Size of image.
        width, height = img.size

        # Start with background if exists to avoid breaking text.
        background = next((op for op in operations if op.get('type') == 'background'), None)
        if background:

            # Remove old background with good quality (spend much time).
            if background['quality']:

                # u2netp 1s, u2net =  2.5s
                model_name = "u2netp"
                rembg_session = new_session(model_name)
                img = remove(img, session=rembg_session)

            # Remove old background with less quality (faster).
            else:

                # Convert PIL image to numpy array format compatible with OpenCV.
                image_np = numpy.array(img)

                # Convert to grayscale image.
                gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)

                # Apply a thresholding method to create a mask.
                _, mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

                # Reverse Mask to remove white pixels.
                mask = 255 - mask

                # Apply mask to original image.
                result = cv2.bitwise_and(image_np, image_np, mask=mask)

                # Convert back the resulting image to PIL format.
                img = Image.fromarray(result)

            # Specific case 'removebackground' => just remove background.
            if background['name'] != 'removebackground':

                # Open background image.
                bg_img = Image.open('backgrounds/' + background['name']).convert("RGBA")

                # Resize background to foreground img size if needed.
                if img.size != bg_img.size:
                    bg_img = bg_img.resize(img.size)
                
                # Combine main image and background.
                img = Image.alpha_composite(bg_img, img)
        
        # Call draw Method to add 2D graphics in an image.
        draw = ImageDraw.Draw(img)

        # Next, add all requested texts on image.
        add_text = [op for op in operations if op.get('type') == 'add_text']
        for params in add_text:

            # Custom font style and font size.
            font_param = ImageFont.truetype(params['font_familly'], params['font_size'])

            # Size of text.
            text_width, text_height = draw.textsize(params['text'], font=font_param)

            # Calculated positions from specific edges.
            x = params['offset'][0]
            y = params['offset'][1]
            positions = {
                'top_left': (x, y),
                'top_right': (width - text_width - x, y),
                'bottom_left': (x, height - text_height - y),
                'bottom_right': (width - text_width - x, height - text_height - y),
                'center': ((width - text_width) // 2, (height - text_height) // 2),
                'center_top': ((width - text_width) // 2, y),
                'center_bottom': ((width - text_width) // 2, height - text_height - y)
            }

            # Position to write.
            final_position = positions[params['from_edge']]
            
            # Add Text to an image
            draw.text(final_position, params['text'], font=font_param, fill=params['color'])

        # Save the edited image
        self._image.seek(0)
        img.save(self._image, format='PNG')
