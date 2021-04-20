# -*- coding: utf-8 -*-

"""
GWHAT License Agreement (GNU-GPLv3)
--------------------------------------

Copyright (c) 2014-2018 GWHAT Project Contributors
https://github.com/jnsebgosselin/gwhat

GWHAT is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>


Spyder License Agreement (MIT License)
--------------------------------------

Copyright (c) Spyder Project Contributors
https://github.com/spyder-ide/spyder

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
"""

import os
import sys


version_info = (0, 5, 0)
__version__ = '.'.join(map(str, version_info))
__appname__ = 'GWHAT'
__namever__ = __appname__ + " " + __version__
__date__ = '07/10/2020'
__project_url__ = "https://github.com/jnsebgosselin/gwhat"
__issues_url__ = __project_url__ + "/issues"
__releases_url__ = __project_url__ + "/releases"
__releases_api__ = "https://api.github.com/repos/jnsebgosselin/gwhat/releases"


def is_frozen():
    """
    Return whether the application is running from a frozen exe or if it
    is running from the Python source files.

    See: https://stackoverflow.com/a/42615559/4481445
    """
    return getattr(sys, 'frozen', False)


def get_versions(reporev=True):
    """
    Return version information for components used by GWHAT

    This function is derived from code that was borrowed from the Spyder
    project, licensed under the terms of the MIT license.
    https://github.com/spyder-ide
    """
    import sys
    import platform

    import qtpy
    import qtpy.QtCore

    # To avoid a crash with Mac app
    if not sys.platform == 'darwin':
        system = platform.system()
    else:
        system = 'Darwin'

    return {
        'version': __version__,
        'python': platform.python_version(),
        'bitness': 64 if sys.maxsize > 2**32 else 32,
        'qt': qtpy.QtCore.__version__,
        'qt_api': qtpy.API_NAME,
        'qt_api_ver': qtpy.PYQT_VERSION,
        'system': system,
        'release': platform.release()}


if is_frozen():
    __rootdir__ = sys._MEIPASS
else:
    __rootdir__ = os.path.dirname(os.path.realpath(__file__))
