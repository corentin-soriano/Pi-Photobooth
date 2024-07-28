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
import os


class Language:
    """
    Class used to replace labels by translated text.

    Attributes:
        _lang_path (str): Language file to use.
    """


    def __init__(self, language = 'english'):
        """
        Init language object with requested lang.

        Args:
            language (str, optional): Language requested, default = english.
        """

        # Get path of trnslation file.
        translations_path = 'templates/translations'
        lang_path = f'{translations_path}/{language}.json'

        # Check if requested language exists.
        if language == '' or not os.path.exists(lang_path):
            lang_path = f'{translations_path}/english.json'

        self._lang_path = lang_path


    def readFile(self):
        """
        Read translation file and returns json.

        Returns:
            str: json with all translations.
        """

        # Read file and return it.
        with open(self._lang_path, 'r') as file:
            return json.load(file)


    def get(self, label):
        """
        Get text for requested label in language file _lang_path.

        Args:
            label (str): Label to translate.

        Returns:
            str: Text for requested label or label itself if not defined.
        """
        
        # Get translations.
        lang = self.readFile()

        try:
            # Return translated label.
            return lang[label]

        except Exception as e:
            print(f"Error Resolving {label}: {str(e)}")
            # Return label if it isn't defined.
            return label
