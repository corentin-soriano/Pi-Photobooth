#!/bin/python3

import easywebdav
import os
import time
from urllib.parse import urlparse
import threading


class WebDAVSync:
    """
    Class used to sync data with webdav.

    Attributes:
        _filename (str): Path for file with data to send.
        _lock (Lock): Lock for read/write in file.
        _webdav (connect): WebDAV client connect object.
        _dav_path (str): Path in webdav.
    """


    def __init__(self, url, username, password, filename = ".webdav-sync"):
        """
        Init attributes and create data file if needed.

        Args:
            url (str): URL of webdav server.
            username (str): Username to use with webdav.
            password (str): Password to use with webdav.
            filename (str, optional): File
        """

        # Create file if needed.
        if not os.path.exists(filename):
            with open(filename, 'w') as file:
                pass
        
        # Split remote URL.
        urlparsed = urlparse(url)
        dest_host = urlparsed.netloc
        dest_path = urlparsed.path
        proto = urlparsed.scheme

        # Init attributes.
        self._lock = threading.Lock()
        self._webdav = easywebdav.connect(dest_host, username=username, password=password, protocol=proto)
        self._filename = filename
        self._dav_path = dest_path


    def add_operation(self, operation, filepath):
        """
        Add pending operation to data queue.

        Args:
            operation (str, optional): Type of operation requested.
            filepath (str): Path of the file.
        """

        # Add new line in file in CSV format.
        with self._lock:
            with open(self._filename, 'a') as f:
                f.write(f"{operation};{filepath}\n")


    def sync(self, stop_event):
        """
        Run dav sync with operations in file.

        Args:
            stop_event (Event): Thread stop event.
        """

        while not stop_event.is_set():
            # Read file.
            with self._lock:
                with open(self._filename, 'r') as file:
                    operation = file.readline().strip()
            
            # No pending operations, exit loop.
            if operation == '':
                break

            # Processing pending operation.
            type = operation.split(';')[0]
            path = operation.split(';')[1]

            while not stop_event.is_set():
                # Send local file to webdav.
                if type == 'push':
                    error = self.push_file(path)
                
                # Exit loop if no error.
                if not error:
                    break

                # Wait 30 seconds before restart operation.
                stop_event.wait(30)
            
            # End of operation, delete it.
            with self._lock:

                # Read file.
                with open(self._filename, 'r') as file:
                    lines = file.readlines()
                
                # Write all lines except the first to tmp file.
                with open(self._filename + '.tmp', 'w') as file_temp:
                    file_temp.writelines(lines[1:])

                # Replace file with the tmp.
                os.replace(self._filename + '.tmp', self._filename)


    def push_file(self, local_path):
        """
        Send local file to WebDAV server.

        Args:
            local_path (str): Path of local file to upload.

        Returns:
            int: exit code (0 = success, error otherwise).
        """

        # Get remote full path.
        remote_path = self._dav_path + '/' + local_path

        # Get webdac client object.
        webdav = self._webdav

        try:

            # Create remote folder if not exists.
            if not webdav.exists(os.path.dirname(remote_path)):
                webdav.mkdir(os.path.dirname(remote_path))

            # Upload file.
            webdav.upload(local_path, remote_path)

            print(f"Image {local_path} uploaded successfully.")
            return 0

        except Exception as e:
            print(f"Error pushing {local_path}: {str(e)}")
            return 1


    def remove_obsolete(self, path):
        """
        Remove obsolete files (local files missing in webdav).

        Args:
            path (str): Path of local folder.

        Returns:
            int: exit code (0 = success, error otherwise).
        """

        # Get remote full path.
        remote_path = self._dav_path + '/' + path

        # Get webdac client object.
        webdav = self._webdav

        try:

            # Create remote folder if not exists.
            if not webdav.exists(remote_path):
                webdav.mkdir(remote_path)

            # Read remote and local files.
            remote_files = webdav.ls(remote_path)
            local_files = os.listdir(path)

            # Filtering filenames.
            remote_files = [os.path.basename(file.name) for file in remote_files if os.path.basename(file.name)]
            local_files = [file for file in local_files if file != 'empty']

            # For each local file, check if exists un remote.
            for file in local_files:

                # Local file doesn't exists in remote.
                if file not in remote_files:

                    filepath = path + '/' + file

                    # If it's a new file, wait more time.
                    difftime = time.time() - os.path.getmtime(filepath)
                    wait_time = 5 * 60

                    # Old file, delete it.
                    if difftime > wait_time:
                        os.remove(filepath)

            return 0

        except Exception as e:
            print(f"Error removing {path}: {str(e)}")
            return 1


    def pull_folder(self, path):
        """
        Pull all remotes files to local folder.

        Args:
            path (str): Path of local folder.

        Returns:
            int: exit code (0 = success, error otherwise).
        """

        # Get remote full path.
        remote_path = self._dav_path + '/' + path

        # Get webdac client object.
        webdav = self._webdav

        try:

            # Create remote folder if not exists.
            if not webdav.exists(remote_path):
                webdav.mkdir(remote_path)

                # Nothing to pull, exit function.
                return 0

            # Read remote and local files.
            remote_files = webdav.ls(remote_path)
            local_files = os.listdir(path)

            # Filtering filenames.
            remote_files = [os.path.basename(file.name) for file in remote_files if os.path.basename(file.name)]
            local_files = [file for file in local_files if file != 'empty']

            # For each local file, check if exists un remote.
            for file in remote_files:

                # Remote file doesn't exists in local.
                if file not in local_files:

                    # Download file.
                    local_filepath = path + '/' + file
                    remote_filepath = remote_path + '/' + file
                    webdav.download(remote_filepath, local_filepath)

            return 0

        except Exception as e:
            print(f"Error pulling {path}: {str(e)}")
            return 1
