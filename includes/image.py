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

import cv2
import numpy
import os
import skimage.exposure
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
                 font_familly='Quicksand-Medium.ttf', color=(255, 255, 255),
                 outline_color = (0,0,0), outline_width = 3):
        """
        Store requested text and parameters to write on commit.

        Args:
            text (str): Text to write.
            offset (tuple): Offset of position (x, y) based on from_edge and img/font size.
            from_edge (str): Position from this edge.
            font_size (int, optional): Font size, default = 20px.
            font_familly (str, optional): Font familly used.
            color (tuple, optional): RGB color of the text. Default = white.
            outline_color (tuple, optional): RGB color of text outline. Default = Black.
            outline_width (int, optional): Width of outline text. Default = 3.
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
            'outline_color': outline_color,
            'outline_width': outline_width,
        }

        # Append params to pending operations.
        self._operations.append(text_params)


    def background(self, name, mirror = False, disable_ai_cut = False, green_background = False):
        """
        Store requested text and parameters to write on commit.

        Args:
            name (str): Name of background file to use.
            mirror (bool, optional): Mirror picture.
            disable_ai_cut (bool, optional): Use AI (rembg/u2net) to cut background.
            green_background (bool, optional): True if using a green background.
        """

        # Dict with requested parameters for this text.
        background_params = {
            'type': 'background',
            'name': name,
            'mirror': mirror,
            'disable_ai_cut': disable_ai_cut,
            'green_background': green_background,
        }

        # Append params to pending operations.
        self._operations.append(background_params)


    def green_background_erase(self, img):
        """
        Removes the green background from an image and returns the image with
        transparency where the green background was.

        This function converts an image with a green background into an image with
        a transparent background by identifying and masking out the green areas.

        Args:
            img (PIL.Image): The input image in PIL format. This image is expected
                             to have a green background.

        Returns:
            PIL.Image: The output image with the green background removed and 
                       replaced by transparency. The output image is in RGBA format.

        """

        # Convert PIL image to numpy array format compatible with OpenCV.
        image_np = numpy.array(img)

        # convert to LAB
        lab = cv2.cvtColor(image_np,cv2.COLOR_BGR2LAB)

        # extract A channel
        A = lab[:,:,1]

        # threshold A channel
        thresh = cv2.threshold(A, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]

        # blur threshold image
        blur = cv2.GaussianBlur(thresh, (0,0), sigmaX=1, sigmaY=1, borderType = cv2.BORDER_DEFAULT)

        # stretch so that 255 -> 255 and 127.5 -> 0
        mask = skimage.exposure.rescale_intensity(blur, in_range=(200,255), out_range=(0,255)).astype(numpy.uint8)

        # add mask to image as alpha channel
        result = image_np.copy()
        result = cv2.cvtColor(image_np, cv2.COLOR_BGR2BGRA)
        result[:,:,3] = mask

        # Convert back the resulting image to PIL format and return it.
        return Image.fromarray(result)


    def white_background_erase(self, img):
        """
        Removes the white background from an image and returns the image with
        transparency where the white background was.

        This function converts an image with a white background into an image with
        a transparent background by identifying and masking out the white areas.

        Args:
            img (PIL.Image): The input image in PIL format. This image is expected
                             to have a white background.

        Returns:
            PIL.Image: The output image with the white background removed and 
                       replaced by transparency. The output image is in RGBA format.
        """

        # Convert PIL image to numpy array format compatible with OpenCV.
        image_np = numpy.array(img)

        # Convert to grayscale image.
        gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)

        # Apply a thresholding method to create a mask.
        _, mask = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)

        # Reverse Mask to remove white pixels.
        mask = 255 - mask

        # Apply mask to original image.
        result = cv2.bitwise_and(image_np, image_np, mask=mask)

        # Convert back the resulting image to PIL format and return it.
        return Image.fromarray(result)


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

            # Remove old background with AI (spend much time).
            if not background['disable_ai_cut']:

                # u2netp 1s, u2net =  2.5s
                model_name = "u2net"
                rembg_session = new_session(model_name)
                img = remove(img, session=rembg_session)

            # Remove old background with opencv2 (faster).
            else:

                # Green background (better).
                if background['green_background']:
                    img = self.green_background_erase(img)

                # White background.
                else:
                    img = self.white_background_erase(img)

            # Check if requested background exists.
            if os.path.exists('backgrounds/' + background['name']):

                # Open background image.
                bg_img = Image.open('backgrounds/' + background['name']).convert("RGBA")

                # Resize background to foreground img size if needed.
                if img.size != bg_img.size:
                    bg_img = bg_img.resize(img.size)

                # Mirror background.
                if background['mirror']:
                    bg_img = bg_img.transpose(Image.FLIP_LEFT_RIGHT)

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
            x, y = positions[params['from_edge']]

            # Draw text outline with position adjustment.
            for adj in range(-params['outline_width'], params['outline_width'] + 1):

                # Draws the text slightly shifted to the right. 
                draw.text((x + adj, y), params['text'], font=font_param, fill=params['outline_color'])
                # Draws the text slightly shifted to the left. 
                draw.text((x - adj, y), params['text'], font=font_param, fill=params['outline_color'])
                # Draws the text slightly shifted to the bottom. 
                draw.text((x, y + adj), params['text'], font=font_param, fill=params['outline_color'])
                # Draws the text slightly shifted to the top. 
                draw.text((x, y - adj), params['text'], font=font_param, fill=params['outline_color'])
                # Draws the text slightly shifted to the right and bottom. 
                draw.text((x + adj, y + adj), params['text'], font=font_param, fill=params['outline_color'])
                # Draws the text slightly shifted to the left and top. 
                draw.text((x - adj, y - adj), params['text'], font=font_param, fill=params['outline_color'])
                # Draws the text slightly shifted to the right and top. 
                draw.text((x + adj, y - adj), params['text'], font=font_param, fill=params['outline_color'])
                # Draws the text slightly shifted to the left and bottom. 
                draw.text((x - adj, y + adj), params['text'], font=font_param, fill=params['outline_color'])

            # Add Text to an image
            draw.text((x, y), params['text'], font=font_param, fill=params['color'])

        # Save the edited image
        self._image.seek(0)
        img.save(self._image, format='PNG')
