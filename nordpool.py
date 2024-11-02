#
#    Nord Pool Day-ahead price data converter
#    Copyright (C) 2016-2024 Cougar <cougar@random.ee>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

""" Parse energy price data from Nord Pool

Parse JSON from Nord Pool Day-ahead price data and output simplified JSON.

For example usage, see at the end of the module.

Command line usage:

    $ cat pricedata.json | python3 -m nordpool
    $ python3 -m nordpool < pricedata.json
    $ python3 -m nordpool pricedata.json
    $ cat pricedata.json | python3 ./nordpool.py
    $ python3 ./nordpool.py < pricedata.json
    $ python3 ./nordpool.py pricedata.json

"""

import sys
import json
from datetime import datetime, timezone

__version__ = "0.3"
__all__ = ['NordPool', 'convert_data']

class NordPool(object):
    """ Nord Pool JSON parser """
    def __init__(self, data):
        self._serverjson = json.loads(data)
        self._pricedata = []

    def _check_data(self):
        """ Simple JSON vaidation check
        """
        if self._serverjson['version'] != 3:
            raise Exception(
                    f"unknown version {self._serverjson['version']}")
        if len(self._serverjson['deliveryAreas']) != 1:
            raise Exception("Only one area is supported")
        if self._serverjson['currency'] != 'EUR':
            raise Exception(
                    f"unknown currency {self._serverjson['currency']}")
        if self._serverjson['areaStates'][0]['state'] != 'Final':
            raise Exception("Not a final data")

    def _parse_data(self):
        """ Parse original Nord Pool JSON to simple time/price list
        """
        self._check_data()
        for row_ in self._serverjson['multiAreaEntries']:
            ts_ = int(datetime
                      .strptime(row_['deliveryStart'], "%Y-%m-%dT%H:%M:%SZ")
                      .replace(tzinfo=timezone.utc)
                      .timestamp()
                      )
            for col_ in row_['entryPerArea']:
                self._pricedata.append({
                    'timestamp': ts_,
                    'val': row_['entryPerArea'][col_],
                    })
                break

    def get_data(self):
        """ Get parsed Nord Pool price data

        :returns: parsed data
        """
        self._parse_data()
        return self._pricedata


def convert_data():
    """ Convert Nord Pool JSON fromat to simple JSON
    """
    if len(sys.argv) == 1:
        infile = sys.stdin
    elif len(sys.argv) == 2:
        infile = open(sys.argv[1], 'r')
    else:
        raise SystemExit(sys.argv[0] + " [infile]")
    with infile:
        obj = NordPool(infile.read()).get_data()
    with sys.stdout:
        json.dump(obj, sys.stdout, sort_keys=True, indent=4)
        sys.stdout.write('\n')


if __name__ == '__main__':
    convert_data()

# vi: set tabstop=2 expandtab textwidth=70 filetype=python:
