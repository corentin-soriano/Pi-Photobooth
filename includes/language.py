#!/bin/python3

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
