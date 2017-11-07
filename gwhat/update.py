# -*- coding: utf-8 -*-
"""
Copyright 2014-2017 Jean-Sebastien Gosselin
email: jean-sebastien.gosselin@ete.inrs.ca

GWHAT is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import requests
import json

# main api url
url = 'https://api.github.com/jnsebgosselin/WHAT/releases'
# url = 'https://github.com/jnsebgosselin/WHAT/releases/tag/4.2.0-beta2'
url = 'https://api.github.com/orgs/octokit/repos'
response = requests.get(url)


#print(dir(response))

# print(response.text)
print(response.json())
