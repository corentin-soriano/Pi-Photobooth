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

import cups
import re
import requests
import os
from PIL import Image


class Printer:
    """
    Class used to print pictures and monitor pending operations.
    
    Attributes:
        _printer (str): Connection to printer.
        _printer_name (str or None): Name of printer or None if unavailable.
    """


    def __init__(self, printer_name = ''):
        """
        Init _printer_name attribute and printer connection.

        Args:
            printer_name (str, optional): Name of printer to use.
        """

        # Store requested printer name before initialization.
        self._printer_name = printer_name

        # Init printer connection if available.
        self.init_printer()


    def init_printer(self):
        """
        Init printer connection.

        Returns:
            int: exit code (0 = success).
        """

        try:
            # Create Cups connection
            self._printer = cups.Connection()
        
            # Get available printers list.
            printers = list(self._printer.getPrinters().keys())

            # No printer available.
            if len(printers) == 0:
                self._printer = None
                return 1

            # If no printer name given or if unavailable, use the first.
            elif self._printer_name == '' or self._printer_name not in printers:
                self._printer_name = printers[0]
            
            # Otherwise, keep self._printer_name value.
            return 0

        # Cups unavailable.
        except Exception as e:
            print(f'Error connecting to cups: {e}')
            self._printer = None
            return 1


    def print(self, filepath):
        """
        Start printing a file from given path.

        Args:
            filepath (str): Path of file to print.

        Returns:
            int: Print job id.
            None: If print failed.
        """

        # List of allowed extensions.
        allowed_extensions = [
            '.jpg',
            '.jpeg',
            '.png'
        ]

        # Get extension of requested file.
        _, extension = os.path.splitext(filepath)

        # Check if printer is ready and retry connection if needed.
        if self._printer == None and self.init_printer() != 0:
            return None

        # Check if file extension is allowed.
        if extension not in allowed_extensions:
            return None
        
        # check if file exists.
        if not os.path.exists(filepath):
            return None

        try:

            # Convert img to pdf for better compatibility.
            pdf_path = '/tmp/' + os.path.basename(filepath) + '.pdf'
            image = Image.open(filepath)
            image = image.convert('RGB')

            # Add light grey padding on img to avoid cutted border.
            padding_px = 50
            width = image.size[0] + padding_px * 2
            height = image.size[1] + padding_px * 2
            color = (230, 230, 230)
            margin_img = Image.new(image.mode, (width, height), color)
            margin_img.paste(image, (padding_px-6, padding_px))

            # Write pdf to disk.
            margin_img.save(pdf_path, "PDF", resolution=100.0)
            
            # Send to printer.
            job_id = self._printer.printFile(self._printer_name, pdf_path, filepath, {})

            # Remove tmp pdf.
            os.remove(pdf_path)

            # Return job id to monitor it after.
            return job_id
        
        except Exception as e:
            print(f'Error printing: {e}')
            self._printer = None
            return None


    def monitor_job(self, job_id):
        """
        Monitor printing job.

        Args:
            job_id (str): ID of job to monitor.

        Returns:
            bool: True if job running, False otherwise.
        """

        # Check if printer is ready and retry connection if needed.
        if self._printer == None and self.init_printer() != 0:
            return None

        try:
            # Get job state.
            job_attrs = self._printer.getJobAttributes(int(job_id))
            job_state = job_attrs['job-state']

            running_states = [
                cups.IPP_JOB_PENDING,
                cups.IPP_JOB_HELD,
                cups.IPP_JOB_PROCESSING
            ]

            # Return job status.
            return job_state in running_states

        except Exception as e:
            print(f'Error monitoring job: {e}')
            self._printer = None
            return False


    def monitor_printer(self):
        """
        Monitor printer state.

        Returns:
            bool: json with printer and paper state.
        """

        # Default values.
        printer_available = self._printer is not None
        paper_amount = 100

        # Check according on printer model.
        if printer_available and 'vc-500w' in self._printer_name.lower():

            try:
                # Call webservice supply info to get media supply.
                response = requests.get('http://vc-500w.host/cgi-bin/getdata?supplyInfo', timeout=2)

            except Exception:
                # Printer unavailable.
                printer_available = False

            # Printer available.
            if printer_available and response.status_code == 200:

                # Get supply length and remaining.
                supply_remaining_match = re.search(
                    r'var\s+supplyRemaining\s*=\s*"(\d+(?:\.\d+){0,1})";',
                    response.text
                )
                supply_length_match = re.search(
                    r'var\s+supplyLength\s*=\s*"(\d+(?:\.\d+){0,1})";',
                    response.text
                )

                # Calculate the remaining percentage.
                if supply_remaining_match and supply_length_match:
                    supply_remaining = float(supply_remaining_match.group(1))
                    supply_length = float(supply_length_match.group(1))
                    paper_amount = int(round((supply_remaining / supply_length) * 100))

                # Missing supply length or remaining.
                else:
                    paper_amount = 0

            # Other http code = printer unavailable.
            else:
                printer_available = False

        return {
            "available": printer_available,
            "paper_amount": paper_amount,
        }

