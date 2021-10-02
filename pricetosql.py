#
#    Save price data from JSON to MySQL
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

""" Read price data from JSON and save to MySQL database

JSON data is a list of price elements where 'timestamp' is UNIX
timestamp and 'val' is a price value (decimal string)

SQL database schema:

    CREATE TABLE IF NOT EXISTS `price` (
      `time` timestamp NOT NULL,
      `price` decimal(5,2) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8;

    ALTER TABLE `price`
      ADD PRIMARY KEY (`time`);

For example usage, see at the end of the module.

Command line usage:

    $ cat data.json | python3 -m pricetosql
    $ python3 -m pricetosql < data.json
    $ python3 -m pricetosql data.json
    $ cat data.json | python3 ./pricetosql.py
    $ python3 ./pricetosql.py < data.json
    $ python3 ./pricetosql.py data.json

"""
import sys
import mysql.connector
import json
import datetime
import decimal

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__version__ = "0.1"
__all__ = ['PriceToSql', 'save_data']

class PriceToSql(object):
    """ Price JSON to SQL writer """
    def __init__(self, dbhost='localhost', dbuser='price', dbpassword='',
                 db='price', table='price'):
        self._dbhost = dbhost
        self._dbuser = dbuser
        self._dbpassword = dbpassword
        self._db = db
        self._table = table
        self._cnx = mysql.connector.connect(user=self._dbuser,
                                            password=self._dbpassword,
                                            host=self._dbhost,
                                            database=self._db)
        self._cnx.cursor().execute("SET SESSION time_zone = '+0:00'")

    def update(self, data):
        """ Update price data in database

        Raise Exception if data already exists but is different
        """
        cursor_ = self._cnx.cursor(buffered=True)
        searchquery_ = ("SELECT price FROM " + self._table + " "
                        "WHERE time = FROM_UNIXTIME(%(timestamp_)s)")
        updatequery_ = ("INSERT INTO " + self._table + " "
                        "(time, price) "
                        "VALUES (FROM_UNIXTIME(%s), %s)")
        for entry_ in data:
            timestamp_ = decimal.Decimal(entry_['timestamp'])
            val_ = decimal.Decimal(entry_['val'])
            cursor_.execute(searchquery_, {'timestamp_': timestamp_})
            for price_ in list(cursor_):
                if price_[0].compare(val_):
                    raise Exception('db entry for %s UTC (%d) is %s but should be %s'
                                    % (datetime.datetime.utcfromtimestamp(entry_['timestamp']), entry_['timestamp'], price_[0], val_))
            if not cursor_.rowcount:
                cursor_.execute(updatequery_, (timestamp_, val_))
                log.info('SQL added %d line: %s',
                          cursor_.rowcount, cursor_.statement)
        self._cnx.commit()
        cursor_.close()
        return


def save_data():
    """ Save JSON price data to the MySQL database
    """
    if len(sys.argv) == 1:
        infile = sys.stdin
    elif len(sys.argv) == 2:
        infile = open(sys.argv[1], 'r')
    else:
        raise SystemExit(sys.argv[0] + " [infile]")
    with infile:
        data = json.load(infile)
    nssdb = PriceToSql(dbpassword='secret')
    nssdb.update(data)


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    save_data()
