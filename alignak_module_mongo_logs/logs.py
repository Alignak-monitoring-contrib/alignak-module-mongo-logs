# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2048: Alignak contrib team, see AUTHORS.txt file for contributors
#
# This file is part of Alignak contrib projet.
#
# Alignak is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Alignak is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Alignak.  If not, see <http://www.gnu.org/licenses/>.

"""
This module is an Alignak Broker module that collects the `monitoring_log` broks to send
them to a Python logger configured in the module configuration file
"""

import re
import time
import datetime
import queue
import logging

from collections import deque

from pymongo import MongoClient
from pymongo.errors import AutoReconnect, ConnectionFailure

from alignak.stats import Stats
from alignak.basemodule import BaseModule

from alignak_module_mongo_logs.logevent import LogEvent

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
for handler in logger.parent.handlers:
    if isinstance(handler, logging.StreamHandler):
        logger.parent.removeHandler(handler)

# pylint: disable=invalid-name
properties = {
    'daemons': ['broker'],
    'type': 'mongo-logs',
    'external': True,
    'phases': ['running'],
}


CONNECTED = 1
DISCONNECTED = 2
SWITCHING = 3


class MongoLogsError(Exception):
    """Specific module exception"""


class UTCFormatter(logging.Formatter):
    """This logging formatter converts the log date/time to UTC"""
    converter = time.gmtime


def get_instance(mod_conf):
    """Return a module instance for the modules manager

    :param mod_conf: the module properties as defined globally in this file
    :return:
    """
    # logger.info("Give an instance of %s for alias: %s",
    # mod_conf.python_name, mod_conf.module_alias)

    return MonitoringLogsCollector(mod_conf)


class MonitoringLogsCollector(BaseModule):
    """Monitoring logs module main class"""
    def __init__(self, mod_conf):
        # pylint: disable=global-statement
        """Module initialization

        mod_conf is a dictionary that contains:
        - all the variables declared in the module configuration file
        - a 'properties' value that is the module properties as defined globally in this file

        :param mod_conf: module configuration file as a dictionary
        """
        BaseModule.__init__(self, mod_conf)

        # pylint: disable=global-statement
        global logger
        logger = logging.getLogger('alignak.module.%s' % self.alias)
        # Do not change log level for this module ...
        # logger.setLevel(getattr(mod_conf, 'log_level', logging.INFO))

        logger.debug("inner properties: %s", self.__dict__)
        logger.debug("received configuration: %s", mod_conf.__dict__)

        # Internal logger for the monitoring logs
        self.logger = None

        stats_host = getattr(mod_conf, 'statsd_host', 'localhost')
        stats_port = int(getattr(mod_conf, 'statsd_port', '8125'))
        stats_prefix = getattr(mod_conf, 'statsd_prefix', 'alignak')
        statsd_enabled = (getattr(mod_conf, 'statsd_enabled', '0') != '0')
        if isinstance(getattr(mod_conf, 'statsd_enabled', '0'), bool):
            statsd_enabled = getattr(mod_conf, 'statsd_enabled')
        graphite_enabled = (getattr(mod_conf, 'graphite_enabled', '0') != '0')
        if isinstance(getattr(mod_conf, 'graphite_enabled', '0'), bool):
            graphite_enabled = getattr(mod_conf, 'graphite_enabled')
        logger.info("StatsD configuration: %s:%s, prefix: %s, enabled: %s, graphite: %s",
                    stats_host, stats_port, stats_prefix, statsd_enabled, graphite_enabled)

        self.statsmgr = Stats()
        # Configure our Stats manager
        if not graphite_enabled:
            self.statsmgr.register(self.alias, 'module',
                                   statsd_host=stats_host, statsd_port=stats_port,
                                   statsd_prefix=stats_prefix, statsd_enabled=statsd_enabled)
        else:
            self.statsmgr.connect(self.alias, 'module',
                                  host=stats_host, port=stats_port,
                                  prefix=stats_prefix, enabled=True)

        self.uri = getattr(mod_conf, 'uri', 'mongodb://localhost')
        logger.info('mongo uri: %s', self.uri)

        # self.replica_set = getattr(mod_conf, 'replica_set', None)
        #
        self.database = getattr(mod_conf, 'database', 'alignak')
        logger.info('database: %s', self.database)

        self.commit_period = int(getattr(mod_conf, 'commit_period', '60'))
        logger.info('periodical commit period: %ds', self.commit_period)

        self.commit_volume = int(getattr(mod_conf, 'commit_volume', '1000'))
        logger.info('periodical commit volume: %d lines', self.commit_volume)

        self.db_test_period = int(getattr(mod_conf, 'db_test_period', '0'))
        logger.info('periodical DB connection test period: %ds', self.db_test_period)

        self.logs_collection = getattr(mod_conf, 'logs_collection', 'logs')
        logger.info('logs collection: %s', self.logs_collection)

        # self.hav_collection = getattr(mod_conf, 'hav_collection', 'availability')
        # logger.info('hosts availability collection: %s', self.hav_collection)

        max_logs_age = getattr(mod_conf, 'max_logs_age', '365')
        maxmatch = re.match(r'^(\d+)([dwmy]*)$', max_logs_age)
        if not maxmatch:
            logger.error("Wrong format for max_logs_age. "
                         "Must be <number>[d|w|m|y] or <number> and not %s", max_logs_age)
            return

        if not maxmatch.group(2):
            self.max_logs_age = int(maxmatch.group(1))
        elif maxmatch.group(2) == 'd':
            self.max_logs_age = int(maxmatch.group(1))
        elif maxmatch.group(2) == 'w':
            self.max_logs_age = int(maxmatch.group(1)) * 7
        elif maxmatch.group(2) == 'm':
            self.max_logs_age = int(maxmatch.group(1)) * 31
        elif maxmatch.group(2) == 'y':
            self.max_logs_age = int(maxmatch.group(1)) * 365
        logger.info('max_logs_age: %s', self.max_logs_age)

        self.is_connected = DISCONNECTED
        self.con = None
        self.db = None

        self.next_logs_rotation = time.time() + 5000

        self.logs_cache = deque()

    def init(self):
        """Handle this module "post" init ; just before it'll be started.

        Like just open necessaries file(s), database(s),
        or whatever the module will need.

        :return: None
        """
        return True

    def do_loop_turn(self):  # pragma: no cover
        """This function is present because of an abstract function in the BaseModule class"""
        logger.info("In loop")
        time.sleep(1)

    def open(self):
        """
        Connect to the Mongo DB with configured URI.

        Execute a command to check if connected on master to activate immediate connection to
        the DB because we need to know if DB server is available.

        Update log rotation time to force a log rotation
        """
        logger.info("trying to connect MongoDB: %s", self.uri)
        self.con = MongoClient(self.uri, connect=False)
        try:
            self.con.admin.command("ismaster")
            logger.info("connected to MongoDB")
            logger.debug("server information: %s", self.con.server_info())

            self.db = getattr(self.con, self.database)
            logger.info("connected to the database: %s", self.database)

            self.is_connected = CONNECTED
            self.next_logs_rotation = time.time()

            logger.info('database connection established')
        except ConnectionFailure as exp:
            logger.error("Server is not available: %s", str(exp))
            return False
        except Exception as exp:
            logger.error("Could not open the database: %s", str(exp))
            raise MongoLogsError

        return True

    def close(self):
        """Close the DB connection"""
        self.is_connected = DISCONNECTED
        self.con.close()
        logger.info('database connection closed')

    def rotate_logs(self):
        """
        For a Mongo DB there is no rotate, but we will delete logs older
        than configured maximum age.
        """
        if not self.is_connected == CONNECTED:
            if not self.open():
                self.next_logs_rotation = time.time() + 600
                logger.info("log rotation failed, next log rotation at %s ",
                            time.asctime(time.localtime(self.next_logs_rotation)))
                return

        logger.info("rotating logs ...")

        now = time.time()
        today = datetime.date.today()
        today0000 = datetime.datetime(today.year, today.month, today.day, 0, 0, 0)
        today0005 = datetime.datetime(today.year, today.month, today.day, 0, 5, 0)
        oldest = today0000 - datetime.timedelta(days=self.max_logs_age)
        result = self.db[self.logs_collection].delete_many({
            u'time': {'$lt': time.mktime(oldest.timetuple())}})
        logger.info("removed %d logs older than %s days.", result.deleted_count, self.max_logs_age)

        if now < time.mktime(today0005.timetuple()):
            next_rotation = today0005
        else:
            next_rotation = today0005 + datetime.timedelta(days=1)

        # See you tomorrow
        self.next_logs_rotation = time.mktime(next_rotation.timetuple())
        logger.info("next log rotation at %s ",
                    time.asctime(time.localtime(self.next_logs_rotation)))

    def commit_logs(self):
        """
        Periodically called (commit_period), this method prepares a bunch of
        queued logs (commit_volume) to insert them in the DB
        """
        if not self.logs_cache:
            self.statsmgr.gauge('committed-logs', 0)
            return

        if not self.is_connected == CONNECTED:
            if not self.open():
                logger.warning("log commiting failed")
                logger.warning("%d lines to insert in database", len(self.logs_cache))
                return

        logger.debug("commiting ...")

        logger.debug("%d lines to insert in database (max insertion is %d lines)",
                     len(self.logs_cache), self.commit_volume)

        # Flush all the stored log lines
        logs_to_commit = 1
        now = time.time()
        some_logs = []
        while True:
            try:
                # result = self.db[self.logs_collection].insert_one(self.logs_cache.popleft())
                some_logs.append(self.logs_cache.popleft())
                logs_to_commit = logs_to_commit + 1
                if logs_to_commit >= self.commit_volume:
                    break
            except IndexError:
                logger.debug("prepared all available logs for commit")
                break
            except Exception as exp:
                logger.error("exception: %s", str(exp))
        logger.debug("time to prepare %s logs for commit (%2.4f)",
                     logs_to_commit, time.time() - now)

        now = time.time()
        try:
            # Insert lines to commit
            result = self.db[self.logs_collection].insert_many(some_logs)
            logger.debug("inserted %d logs.", len(result.inserted_ids))
            self.statsmgr.gauge('committed-logs', len(result.inserted_ids))

            # Request the server to flush data on files
            self.con.fsync(async=True)
        except AutoReconnect as exp:
            self.statsmgr.gauge('committed-logs', 0)
            logger.error("Auto-reconnect exception when inserting lines: %s", str(exp))
            self.is_connected = SWITCHING
            # Abort commit ... will be finished next time!
        except Exception as exp:
            self.statsmgr.gauge('committed-logs', 0)
            self.close()
            logger.error("Database error occurred when committing: %s", exp)
        logger.debug("time to insert %s logs (%2.4f)", logs_to_commit, time.time() - now)

    def manage_log_brok(self, brok):
        """
        Parse a monitoring log brok to enqueue a log line for DB insertion

        Brok 8120c349-b1f3-473f-bf2e-9909d4c00a5d (2019-12-17 09:04:02.776266) 'monitoring_log':
        {
            'instance_id': u'SchedulerLink_1',
            u'message': u'SERVICE ALERT: my-mongo-primary;Up-to-date;UNKNOWN;HARD;4;
                CHECK_NRPE STATE UNKNOWN: Socket timeout after 10 seconds.',
            u'level': u'info'
        }

        :return: False if the data are not useful, else True
        """
        # Try to get a monitoring event from the brok data
        try:
            event = LogEvent(('[%s] ' % int(time.time())) + brok.data['message'])
            if not event.valid:
                logger.warning("No monitoring event detected from: %s", brok.data['message'])
                return False
            logger.debug("Detected: %s", event)

            # -------------------------------------------
            # Add an history event
            metric = event.pattern.strip().replace(" ", "_")
            self.statsmgr.counter('monitoring-event-got.%s' % metric, 1)

            if event.pattern not in ['TIMEPERIOD TRANSITION', 'RETENTION LOAD', 'RETENTION SAVE',
                                     'CURRENT STATE', 'NOTIFICATION', 'ALERT', 'DOWNTIME',
                                     'FLAPPING', 'ACTIVE CHECK', 'PASSIVE CHECK',
                                     'COMMENT', 'ACKNOWLEDGE', 'DOWNTIME']:
                self.statsmgr.counter('monitoring-event-ignored.%s' % metric, 1)
                logger.debug("Monitoring event not stored in the DB: %s",
                             brok.data['message'])
                return False

            data = {
                'message': brok.data['message']
            }
            data.update(event.data)

            logger.debug('store log line values: %s', data)
            self.logs_cache.append(data)

        except ValueError:
            logger.warning("Unable to decode a monitoring event from: %s", brok.data['message'])

        return True

    def manage_brok(self, brok):
        """We got the data to manage

        :param brok: Brok object
        :type brok: alignak.brok.Brok
        :return: False if a backend post error happens
        """
        logger.debug("manage brok: %s", brok.type)
        # Ignore all except 'monitoring_log' broks...
        if brok.type not in ['monitoring_log']:
            return False

        # Do not care about level information!
        # level = brok.data['level'].lower()
        # if level not in ['debug', 'info', 'warning', 'error', 'critical']:
        #     return False

        logger.debug("Got a monitoring log brok: %s", brok)
        return self.manage_log_brok(brok)

    def main(self):
        """Main loop of the process

        This module is an "external" module
        :return:
        """
        # Set the OS process title
        self.set_proctitle(self.alias)
        self.set_exit_handler()

        logger.info("starting...")

        # Open database connection
        self.open()

        logger.info("DB opened")

        db_commit_next_time = time.time()
        db_test_connection = time.time()

        while not self.interrupted:
            logger.debug("queue length: %s", self.to_q.qsize())
            now = time.time()

            # DB connection test ?
            if self.db_test_period and db_test_connection < now:
                logger.info("Testing database connection ...")
                # Test connection periodically...
                db_test_connection = now + self.db_test_period
                if self.is_connected == DISCONNECTED:
                    logger.warning("Trying to connect database ...")
                    self.open()

            # Logs commit ?
            if db_commit_next_time < now:
                logger.debug("Logs commit time ...")
                # Commit periodically ...
                db_commit_next_time = now + self.commit_period
                self.commit_logs()

            # Logs rotation ?
            if self.next_logs_rotation < now:
                logger.debug("Logs rotation time ...")
                self.rotate_logs()

            # Broks management ...
            try:
                queue_size = self.to_q.qsize()
                if queue_size:
                    logger.debug("queue length: %s", queue_size)
                    self.statsmgr.gauge('queue-size', queue_size)

                message = self.to_q.get_nowait()
                start = time.time()
                for brok in message:
                    # Prepare and manage each brok in the queue message
                    brok.prepare()
                    self.manage_brok(brok)

                logger.debug("time to manage %s broks (%d secs)", len(message), time.time() - start)
                self.statsmgr.timer('managed-broks-time', time.time() - start)
            except queue.Empty:
                # logger.debug("No message in the module queue")
                time.sleep(0.1)

        logger.info("stopping...")

        # Close database connection
        self.close()

        # Properly close all the Python logging stuff
        # See: http://stackoverflow.com/questions/24816456/python-logging-wont-shutdown
        logging.shutdown()

        logger.info("stopped")
