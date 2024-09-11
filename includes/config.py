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

import configparser
from time import sleep


class ConfigFile:
    """
    Class used to manage project config file with ini format.

    Attributes:
        _filename (str): Path for ini config file.
        _config (ConfigParser): ConfigParser object.
    """


    def __init__(self, filename='config.ini'):
        """
        Init _config and _filename.

        Args:
            filename (str, optional): Path for ini config file.
                                      Default name is config.ini but can be modified.
        """

        # Store filename.
        self._filename = filename

        # Init configparser.
        self._config = configparser.RawConfigParser()


    def get(self, section, key, max_retries=5):
        """
        Get value from config file.

        Args:
            section (str): [section] of ini.
            key (str): Key to read in section.

        Returns:
            str: value of requested key.
        """

        # Read ini file on disk.
        self._config.read(self._filename)

        # Read requested key on file.
        value = self._config.get(section, key, fallback='')

        # Retry if read error.
        if not isinstance(value, str) and max_retries > 0:
            print(f"Error reading {key} (remaining tries: {max_retries})...")
            sleep(0.25)
            value = self.get(section, key, max_retries-1)
        
        if not isinstance(value, str) and max_retries == 0:
            print(f"Error reading {key}, set default value = '' (empty str).")
            value = ''

        return value


    def set(self, section, key, value):
        """
        Update value in config file.

        Args:
            section (str): [section] of ini.
            key (str): Key to read in section.
            value (str): New value to write.
        """

        # Read ini file.
        self._config.read(self._filename)

        # Update configuration.
        self._config[section][key] = str(value)

        # Save updated configuration.
        with open(self._filename, 'w') as configfile:
            self._config.write(configfile)
