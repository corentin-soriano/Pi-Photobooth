#!/bin/python3

import qrcode
from io import BytesIO
from PIL import Image, ImageDraw


def str_to_bool(string):
    """
    Converts str to bool.

    Args:
        string (str): String to convert

    Returns:
        bool or None: True if the string matches a true value,
                      False if it matches a false value,
                      None otherwise.
    """
    true_values = ['true', '1', 't', 'y', 'yes', 'on']
    false_values = ['false', '0', 'f', 'n', 'no', 'off']
    
    if string.lower() in true_values:
        return True
    elif string.lower() in false_values:
        return False
    else:
        return None


def generate_qrcode(data):
    """
    Generate qrcodes with given data.

    Args:
        data (str): The data to write on qrcode.

    Returns:
        Response: The qrcode image (PNG format).
    """

    # QRCode configuration.
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    # Add URL in qrcode data.
    qr.add_data(data)

    # Make qrcode.
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="transparent")

    # Use PIL to edit image.
    qr_pil = qr_img.convert('RGBA')

    # Create gradient Green to red.
    width, height = qr_pil.size
    gradient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(gradient)
    for y in range(height):
        r = int(220 * (y / height))
        g = int(255 * (1 - y / height))
        b = int(255 * (y / height))
        draw.line((0, y, width, y), fill=(r, g, b, 255))

    # Apply gradient on qrcode image using a mask on black pixels.
    mask = qr_pil.split()[3]
    qr_colored = Image.composite(gradient.transpose(Image.ROTATE_270), qr_pil, mask)

    # Save qrcode in BytesIO stream.
    qr_bytes = BytesIO()
    qr_colored.save(qr_bytes, format='PNG')
    qr_bytes.seek(0)

    # Send qrcode.
    return qr_bytes

