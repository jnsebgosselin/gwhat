# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

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
