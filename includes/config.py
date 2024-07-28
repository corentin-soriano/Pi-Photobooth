#!/bin/python3

import configparser


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
        self._config = configparser.ConfigParser()


    def get(self, section, key):
        """
        Get value from config file.

        Args:
            section (str): [section] of ini.
            key (str): Key to read in section.

        Returns:
            str: value of requested key.
        """

        # Read ini file.
        self._config.read(self._filename)

        return self._config.get(section, key, fallback=None)


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
        self._config[section][key] = value

        # Save updated configuration.
        with open(self._filename, 'w') as configfile:
            self._config.write(configfile)
