# -*- coding: utf-8 -*-

# Copyright (c) 2014-2017 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# Copyright (c) 2017 Spyder Project Contributors
# https://github.com/spyder-ide/spyder
#
# Copyright (C) 2013 The IPython Development Team
# https://github.com/ipython/ipython
#
# This file is a derivative work of codes from the files updates.py and
# programs.py of the Spyder project.
# Licensed under the terms of the MIT License.
#
# https://github.com/spyder-ide/spyder/master/spyder/workers/updates.py
# https://github.com/spyder-ide/spyder/blob/master/spyder/utils/programs.py
#
# See gwhat/__init__.py for more details.


# ---- Imports: standard libraries

import json
import ssl
import re
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from distutils.version import LooseVersion


# ---- Imports: third parties

from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSlot as QSlot
from PyQt5.QtCore import pyqtSignal as QSignal


# ---- Imports: local

from gwhat import __version__, __releases_url__


class WorkerUpdates(QObject):
    """
    Worker that checks for releases using the Github API.

    Copyright (c) Spyder Project Contributors
    Licensed under the terms of the MIT License
    """
    sig_ready = QSignal(bool, str)

    def __init__(self):
        super(WorkerUpdates, self).__init__()
        self.error = None
        self.latest_release = None

    def start(self):
        """Main method of the WorkerUpdates worker."""
        self.update_available = False
        self.latest_release = __version__
        error_msg = None
        try:
            if hasattr(ssl, '_create_unverified_context'):
                # Fix for Spyder issue #2685.
                context = ssl._create_unverified_context()
                page = urlopen(__releases_url__, context=context)
            else:
                page = urlopen(__releases_url__)
            try:
                data = page.read().decode()
                data = json.loads(data)

                releases = [item['tag_name'].replace('gwhat-', '')
                            for item in data
                            if item['tag_name'].startswith("gwhat")]
                version = __version__

                result = check_update_available(version, releases)
                self.update_available, self.latest_release = result
            except Exception:
                error_msg = ('Unable to retrieve information.')
        except HTTPError:
            error_msg = ('Unable to retrieve information.')
        except URLError:
            error_msg = ('Unable to connect to the internet. <br><br>Make '
                         'sure the connection is working properly.')
        except Exception:
            error_msg = ('Unable to check for updates.')

        # Don't show dialog when starting up spyder and an error occur
        if error_msg is None:
            print(self.update_available, self.latest_release)
            self.error = error_msg
            self.sig_ready.emit(self.update_available, self.latest_release)


def check_update_available(version, releases):
    """
    Checks if there is an update available.

    It takes as parameters the current version of GWHAT and a list of
    valid cleaned releases in chronological order (what github api returns
    by default). Example: ['2.3.4', '2.3.3' ...]

    Copyright (c) Spyder Project Contributors
    Licensed under the terms of the MIT License
    """
    if is_stable_version(version):
        # Remove non stable versions from the list
        releases = [r for r in releases if is_stable_version(r)]

    latest_release = releases[0]
    if version.endswith('dev'):
        print("coucou")
        return (False, latest_release)
    else:
        return (check_version(version, latest_release, '<'),
                latest_release)


def check_version(actver, version, cmp_op):
    """
    Check version string of an active module against a required version.

    If dev/prerelease tags result in TypeError for string-number comparison,
    it is assumed that the dependency is satisfied. Users on dev branches are
    responsible for keeping their own packages up to date.

    Copyright (C) 2013 The IPython Development Team
    Licensed under the terms of the BSD License
    """
    if isinstance(version, tuple):
        version = '.'.join([str(i) for i in version])

    # Hacks needed so that LooseVersion understands that (for example)
    # version = '3.0.0' is in fact bigger than actver = '3.0.0rc1'
    if (is_stable_version(version) and not is_stable_version(actver) and
            actver.startswith(version) and version != actver):
        version = version + 'zz'
    elif (is_stable_version(actver) and not is_stable_version(version) and
            version.startswith(actver) and version != actver):
        actver = actver + 'zz'

    try:
        if cmp_op == '>':
            return LooseVersion(actver) > LooseVersion(version)
        elif cmp_op == '>=':
            return LooseVersion(actver) >= LooseVersion(version)
        elif cmp_op == '=':
            return LooseVersion(actver) == LooseVersion(version)
        elif cmp_op == '<':
            return LooseVersion(actver) < LooseVersion(version)
        elif cmp_op == '<=':
            return LooseVersion(actver) <= LooseVersion(version)
        else:
            return False
    except TypeError:
        return True


def is_stable_version(version):
    """
    Returns wheter this is a stable version or not. A stable version has no
    letters in the final component, but only numbers.

    Stable version example: 1.2, 1.3.4, 1.0.5
    Not stable version: 1.2alpha, 1.3.4beta, 0.1.0rc1, 3.0.0dev

    Copyright (c) Spyder Project Contributors
    Licensed under the terms of the MIT License
    """
    if not isinstance(version, tuple):
        version = version.split('.')
    last_part = version[-1]

    if not re.search('[a-zA-Z]', last_part):
        return True
    else:
        return False


if __name__ == "__main__":
    updates_worker = WorkerUpdates()
    updates_worker.start()
