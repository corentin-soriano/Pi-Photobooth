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

# Newer raspberry devices.
import gpiod
# Legacy.
import RPi.GPIO as GPIO


class ManageGPIO:
    """
    Class used to manage RPI GPIO.

    Attributes:
        _legacy (bool): To use an older raspberrypi.
        _chip (Chip): gpiod context
    """


    def __init__(self, legacy):
        """
        Init object and store legacy mode status.

        Args:
            legacy (bool): To use an older raspberrypi.
        """

        self._legacy = legacy
        self._chip = gpiod.find_line('ID_SDA').owner()


    def setup_pin(self, pin):
        """
        Setup pin as internal pull-up.

        Add button between GND and PIN.

        Args:
            pin (int): Pin number.
        """

        if self._legacy:
            GPIO.setmode(GPIO.BCM)
            # Setup GPIO pin with internal pull-up.
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        else:
            line = self._chip.get_line(pin)
            line.request(consumer='pull_up_button',
                         type=gpiod.LINE_REQ_DIR_IN,
                         flags=gpiod.LINE_REQ_FLAG_BIAS_PULL_UP)


    def get_state(self, pin):
        """
        Get GPIO state from its number.

        Args:
            pin (int): Pin number.

        Returns:
            bool: State of requested pin.
        """

        if self._legacy:
            return GPIO.input(pin) == GPIO.LOW
        
        else:
            line = self._chip.get_line(pin)
            return not line.get_value()


    def cleanup(self, pins = None):
        """
        Close GPIO.

        Args:
            pin (list, optional): pins numbers to close when not in legacy mode.
        """

        if self._legacy:
            GPIO.cleanup()

        else:

            # Close all lines.
            for pin in pins:
                line = self._chip.get_line(pin)
                line.release()

            # Close context.
            self._chip.close()
