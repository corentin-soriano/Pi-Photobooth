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

import json
import requests


class webhook:
    """
    Class used to sent push notifications via webhook.

    Attributes:
        _url (str): URL of webhook.
        _headers (str): Headers for this webhook.
        _data (str): Data for this webhook (override %MSG%).
        _memory (dict): Memory of old messages.
    """


    def __init__(self, url, headers, data):
        """
        Init attributes and create data file if needed.

        Args:
            url (str): URL of webdav server.
            headers (str): Username to use with webdav.
            data (str): Password to use with webdav.
        """
        
        self._url = url
        self._headers = headers
        self._data = data
        self._memory = {}


    def _send_webhook(self, data):
        """
        Send webhook request.

        Args:
            data (str): Raw POST data.
        
        Returns:
            int: exit code (0 = ok).
        """

        try:
            headers = json.loads(self._headers)
            response = requests.post(self._url, data=data, headers=headers, timeout=2)
            return 0
        except Exception:
            print("Error while sending webhook.")
            return 1


    def send(self, name, message):
        """
        Send webhook after check previous state in memory.

        Args:
            name (str): Name of metric.
            message (str): Message associated to metric.
        """

        # Check if metric exists in memory. Send only if last value is different.
        if name in self._memory and self._memory[name] == message:
            return

        # Replace %MSG% marker in data.
        data = self._data.replace("%MSG%", f'**{name}:** *{message}*')

        # Send webhook.
        error = self._send_webhook(data)

        # Update metric in memory if no error.
        if not error:
            self._memory[name] = message
