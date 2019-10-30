#
#    NordSpoolSpot Elspot energy price data converter
#    Copyright (C) 2016 Cougar <cougar@random.ee>
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

""" Parse energy price data from NordSpoolSpot

Parse JSON data from www.nordpoolspot.com and output simplified JSON.

For example usage, see at the end of the module.

Command line usage:

    $ cat pricedata.json | python3 -m nordspoolspot
    $ python3 -m nordspoolspot < pricedata.json
    $ python3 -m nordspoolspot pricedata.json
    $ cat pricedata.json | python3 ./nordspoolspot.py
    $ python3 ./nordspoolspot.py < pricedata.json
    $ python3 ./nordspoolspot.py pricedata.json

"""

import sys
import json
import os
import time
from datetime import datetime,timedelta
from pytz import timezone

__version__ = "0.2"
__all__ = ['NordSpoolSpot', 'convert_data']

TIMEZONE = 'Europe/Paris'

class NordSpoolSpot(object):
    """ NordSpoolSpot JSON parser """
    def __init__(self, data):
        self._serverjson = json.loads(data)
        self._pricedata = []

    def _check_data(self):
        """ Simple JSON vaidation check
        """
        if self._serverjson['currency'] != 'EUR':
            raise Exception('invalid currency %s',
                            self._serverjson['currency'])
        if self._serverjson['pageId'] != 47:
            raise Exception('invalid pageId %s',
                            self._serverjson['pageId'])

    def _parse_data(self):
        """ Parse original NordSpoolSpot JSON to simple time/price list
        """
        self._check_data()
        os.environ['TZ'] = 'CET'
        time.tzset()
        last_starttime = None
        for row_ in self._serverjson['data']['Rows']:
            if row_['IsExtraRow']:
                continue
            ts_ = parsetime(row_['StartTime'], row_['StartTime'] !=
                            last_starttime)
            last_starttime = row_['StartTime']
            for col_ in row_['Columns']:
                if col_['Value'] == '-':
                    break
                self._pricedata.append({
                    'timestamp': ts_,
                    'val': col_['Value'].replace(',', '.')
                    })
                break

    def get_data(self):
        """ Get parsed NordSpoolSpot price data

        :returns: parsed data
        """
        self._check_data()
        self._parse_data()
        return self._pricedata


def convert_data():
    """ Convert NordSpoolSpot JSON fromat to simple JSON
    """
    if len(sys.argv) == 1:
        infile = sys.stdin
    elif len(sys.argv) == 2:
        infile = open(sys.argv[1], 'r')
    else:
        raise SystemExit(sys.argv[0] + " [infile]")
    with infile:
        obj = NordSpoolSpot(infile.read()).get_data()
    with sys.stdout:
        json.dump(obj, sys.stdout, sort_keys=True, indent=4)
        sys.stdout.write('\n')


def parsetime(timestr, is_dst=True):
    _st = time.strptime(timestr, '%Y-%m-%dT%H:%M:%S')
    _dt = datetime(_st.tm_year, _st.tm_mon, _st.tm_mday, _st.tm_hour,
                    _st.tm_min, _st.tm_sec)
    return int(datetime.timestamp(timezone(TIMEZONE).localize(_dt, is_dst=is_dst)))


if __name__ == '__main__':
    convert_data()
