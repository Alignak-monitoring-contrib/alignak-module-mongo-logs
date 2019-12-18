#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016: Alignak team, see AUTHORS.txt file for contributors
#
# This file is part of Alignak.
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
#
"""
Test the module
"""

import re
import os
import time
import pytest
from freezegun import freeze_time

from alignak_test import AlignakTest
from alignak.modulesmanager import ModulesManager
from alignak.objects.module import Module
from alignak.basemodule import BaseModule
from alignak.brok import Brok

# Set environment variable to ask code Coverage collection
os.environ['COVERAGE_PROCESS_START'] = '.coveragerc'

import alignak_module_mongo_logs


class TestModules(AlignakTest):
    """
    This class contains the tests for the module
    """

    def _assert_logs_queue(self, instance, ref_logs):
        some_logs = []
        while True:
            try:
                # result = self.db[self.logs_collection].insert_one(self.logs_cache.popleft())
                some_logs.append(instance.logs_cache.popleft())
            except IndexError:
                break

        self.assertEqual(ref_logs, some_logs)

    @freeze_time("2017-06-01 18:30:00")
    def test_module_default_configuration(self):
        """Test the module initialization function, no parameters, using default
        :return:
        """
        # Obliged to call to get a self.logger...
        self.setup_with_file('etc/cfg_default.cfg')
        self.assertTrue(self.conf_is_correct)

        # Clear logs
        self.clear_logs()

        # -----
        # Default initialization
        # -----
        # Create a module instance
        mod = Module({
            'module_alias': 'logs',
            'module_types': 'logs',
            'python_name': 'alignak_module_mongo_logs',
            'uri': 'mongodb://localhost',
            'database': 'alignak-test',
            'db_test_period': '300',
            'logs_collection': 'logs-test',
            'commit_volume': '1000',
            'commit_period': '60',
            'max_logs_age': '365'
        })

        instance = alignak_module_mongo_logs.get_instance(mod)
        self.assertIsInstance(instance, BaseModule)

        i = 0
        self.assert_log_match(re.escape(
            "StatsD configuration: localhost:8125, prefix: alignak, enabled: False, graphite: False"
        ), i)
        i += 1
        self.assert_log_match(re.escape(
            "mongo uri: mongodb://localhost"
        ), i)
        i += 1
        self.assert_log_match(re.escape(
            "database: alignak"
        ), i)
        i += 1
        self.assert_log_match(re.escape(
            "periodical commit period: 60s"
        ), i)
        i += 1
        self.assert_log_match(re.escape(
            "periodical commit volume: 1000 lines"
        ), i)
        i += 1
        self.assert_log_match(re.escape(
            "periodical DB connection test period: 300s"
        ), i)
        i += 1
        self.assert_log_match(re.escape(
            "logs collection: logs-test"
        ), i)
        i += 1
        self.assert_log_match(re.escape(
            "max_logs_age: 365"
        ), i)

        # --------------------
        # Raise some broks
        # --------------------

        # Unknown brok type
        # --------------------
        b = Brok({'type': 'unknown', 'data': {'level': 'info', 'message': 'test message'}})
        b.prepare()
        assert instance.manage_brok(b) is False

        # Unknown log level
        # --------------------
        b = Brok({'type': 'monitoring_log', 'data': {'level': 'unknown', 'message': 'test message'}})
        b.prepare()
        assert instance.manage_brok(b) is False

        # Unparsable log message
        # --------------------
        b = Brok({'type': 'monitoring_log', 'data': {'level': 'info', 'message': 'test message'}})
        b.prepare()
        result = instance.manage_brok(b)
        self.show_logs()
        assert result is False

        # Timeperiod transition
        # --------------------
        b = Brok({'type': 'monitoring_log', 'data': {
            'level': 'info',
            'message': 'TIMEPERIOD TRANSITION: 24x7;-1;1'
        }})
        b.prepare()
        result = instance.manage_brok(b)
        self.show_logs()
        print(instance.logs_cache)
        self._assert_logs_queue(instance, [
            {'time': 1496341800.0, 'message': 'TIMEPERIOD TRANSITION: 24x7;-1;1',
             'plugin_output': '24x7;-1;1', 'type': 'TIMEPERIOD TRANSITION'}
        ])
        assert result is True

        b = Brok({'type': 'monitoring_log', 'data': {
            'level': 'info',
            'message': 'RETENTION LOAD: scheduler'
        }})
        b.prepare()
        result = instance.manage_brok(b)
        self.show_logs()
        print(instance.logs_cache)
        self._assert_logs_queue(instance, [
            {'time': 1496341800.0, 'message': 'RETENTION LOAD: scheduler',
             'plugin_output': 'scheduler', 'type': 'RETENTION LOAD'}
        ])
        assert result is True

        b = Brok({'type': 'monitoring_log', 'data': {
            'level': 'info',
            'message': 'RETENTION SAVE: scheduler'
        }})
        b.prepare()
        result = instance.manage_brok(b)
        self.show_logs()
        print(instance.logs_cache)
        self._assert_logs_queue(instance, [
            {'time': 1496341800.0, 'message': 'RETENTION SAVE: scheduler',
             'plugin_output': 'scheduler', 'type': 'RETENTION SAVE'}
        ])
        assert result is True

        b = Brok({'type': 'monitoring_log', 'data': {
            'level': 'info',
            'message': 'SERVICE ALERT: cogny;Load;OK;HARD;4;OK - load average: 0.74, 0.89, 1.03'
        }})
        b.prepare()
        result = instance.manage_brok(b)
        self.show_logs()
        print(instance.logs_cache)
        self._assert_logs_queue(instance, [
            {'time': 1496341800.0,
             'message': 'SERVICE ALERT: cogny;Load;OK;HARD;4;OK - load average: 0.74, 0.89, 1.03',
             'plugin_output': 'OK - load average: 0.74, 0.89, 1.03',
             'type': 'SERVICE ALERT',
             'state': 'OK', 'state_type': 'HARD',
             'attempts': 4,
             'host_name': 'cogny', 'service_description': 'Load'}
        ])
        assert result is True

        b = Brok({'type': 'monitoring_log', 'data': {
            'level': 'warning',
            'message': 'SERVICE NOTIFICATION: notified;north_host_001;dummy_critical;CRITICAL;1;'
                       'notify-service-by-log;north_host_001-dummy_critical-2 is ko'
        }})
        b.prepare()
        result = instance.manage_brok(b)
        self.show_logs()
        print(instance.logs_cache)
        self._assert_logs_queue(instance, [
            {'time': 1496341800.0,
             'message': 'SERVICE NOTIFICATION: notified;north_host_001;dummy_critical;CRITICAL;1;'
                        'notify-service-by-log;north_host_001-dummy_critical-2 is ko',
             'plugin_output': 'north_host_001-dummy_critical-2 is ko',
             'type': 'SERVICE NOTIFICATION',
             'command_name': 'notify-service-by-log', 'contact_name': 'notified',
             'state': 'CRITICAL', 'notification_number': '1',
             'host_name': 'north_host_001', 'service_description': 'dummy_critical'}
        ])
        assert result is True

        b = Brok({'type': 'monitoring_log', 'data': {
            'level': 'info',
            'message': 'CURRENT SERVICE STATE: lachassagne;Zombies;'
                       'OK;HARD;1;PROCS OK: 0 processes with STATE = Z'
        }})
        b.prepare()
        result = instance.manage_brok(b)
        self.show_logs()
        print(instance.logs_cache)
        #
        #
        # Unhandled message!
        #
        #
        self._assert_logs_queue(instance, [])
        assert result is True

        # Host acknowledgement:
        # [2019-12-18 08:52:21] INFO: HOST ACKNOWLEDGE ALERT: my-elasticsearch-es1;STARTED;
        # Host problem has been acknowledged
        # [2019-12-18 08:52:24] INFO: HOST ACKNOWLEDGE ALERT: my-elasticsearch-es1;EXPIRED;
        # Host problem acknowledge expired
        b = Brok({'type': 'monitoring_log', 'data': {
            'level': 'error',
            'message': 'HOST ACKNOWLEDGE ALERT: my-elasticsearch-es1;STARTED; '
                       'Host problem has been acknowledged'
        }})
        b.prepare()
        result = instance.manage_brok(b)
        self.show_logs()
        print(instance.logs_cache)
        self._assert_logs_queue(instance, [
            {'time': 1496341800.0,
             'message': 'HOST ACKNOWLEDGE ALERT: my-elasticsearch-es1;STARTED; '
                        'Host problem has been acknowledged',
             'plugin_output': ' Host problem has been acknowledged',
             'type': 'HOST ACKNOWLEDGE',
             'state': 'STARTED',
             'host_name': 'my-elasticsearch-es1', 'service_description': ''}
        ])
        assert result is True

        b = Brok({'type': 'monitoring_log', 'data': {
            'level': 'error',
            'message': 'HOST ACKNOWLEDGE ALERT: my-elasticsearch-es1;EXPIRED; '
                       'Host problem has been acknowledged'
        }})
        b.prepare()
        result = instance.manage_brok(b)
        self.show_logs()
        print(instance.logs_cache)
        self._assert_logs_queue(instance, [
            {'time': 1496341800.0,
             'message': 'HOST ACKNOWLEDGE ALERT: my-elasticsearch-es1;EXPIRED; '
                        'Host problem has been acknowledged',
             'plugin_output': ' Host problem has been acknowledged',
             'type': 'HOST ACKNOWLEDGE',
             'state': 'EXPIRED',
             'host_name': 'my-elasticsearch-es1', 'service_description': ''}
        ])
        assert result is True

        # Service acknowledgement:
        # [2019-12-18 08:52:21] INFO: SERVICE ACKNOWLEDGE ALERT: my-elasticsearch-es1;
        # check-es-http-alive;STARTED; Service problem has been acknowledged
        b = Brok({'type': 'monitoring_log', 'data': {
            'level': 'error',
            'message': 'SERVICE ACKNOWLEDGE ALERT: my-elasticsearch-es1;check-es-http-alive;'
                       'STARTED; Service problem has been acknowledged'
        }})
        b.prepare()
        result = instance.manage_brok(b)
        self.show_logs()
        print(instance.logs_cache)
        self._assert_logs_queue(instance, [
            {'time': 1496341800.0,
             'message': 'SERVICE ACKNOWLEDGE ALERT: my-elasticsearch-es1;check-es-http-alive;'
                        'STARTED; Service problem has been acknowledged',
             'plugin_output': ' Service problem has been acknowledged',
             'type': 'SERVICE ACKNOWLEDGE',
             'state': 'STARTED',
             'host_name': 'my-elasticsearch-es1', 'service_description': 'check-es-http-alive'}
        ])
        assert result is True

        # Host downtimes
        # [2019-12-18 09:19:01] INFO: HOST DOWNTIME ALERT: my-secured-elasticsearch-es2;STARTED;
        # Host has entered a period of scheduled downtime
        # [2019-12-18 09:19:01] INFO: HOST NOTIFICATION: notified;my-secured-elasticsearch-es2;
        # DOWNTIMESTART (DOWN);2;notify-host-by-log;CHECK_NRPE STATE UNKNOWN: Socket timeout after 10 seconds.
        # [2019-12-18 09:20:00] INFO: HOST DOWNTIME ALERT: my-secured-elasticsearch-es2;STOPPED;
        # Host has exited from a period of scheduled downtime
        # [2019-12-18 09:20:00] INFO: HOST NOTIFICATION: notified;my-secured-elasticsearch-es2;
        # DOWNTIMEEND (DOWN);2;notify-host-by-log;CHECK_NRPE STATE UNKNOWN: Socket timeout after 10 seconds.
        b = Brok({'type': 'monitoring_log', 'data': {
            'level': 'error',
            'message': 'HOST DOWNTIME ALERT: my-secured-elasticsearch-es2;STARTED; '
                       'Host has entered a period of scheduled downtime'
        }})
        b.prepare()
        result = instance.manage_brok(b)
        self.show_logs()
        print(instance.logs_cache)
        self._assert_logs_queue(instance, [
            {'time': 1496341800.0,
             'message': 'HOST DOWNTIME ALERT: my-secured-elasticsearch-es2;STARTED; '
                        'Host has entered a period of scheduled downtime',
             'plugin_output': ' Host has entered a period of scheduled downtime',
             'type': 'HOST DOWNTIME',
             'state': 'STARTED',
             'host_name': 'my-secured-elasticsearch-es2', 'service_description': ''}
        ])
        assert result is True


        # [2019-12-18 09:19:01] INFO: SERVICE DOWNTIME ALERT: my-secured-elasticsearch-es2;
        # check-es-http-alive;STARTED; Service has entered a period of scheduled downtime
        b = Brok({'type': 'monitoring_log', 'data': {
            'level': 'info',
            'message': 'SERVICE DOWNTIME ALERT: my-secured-elasticsearch-es2;check-es-http-alive;'
                       'STARTED; Service has entered a period of scheduled downtime'
        }})
        b.prepare()
        result = instance.manage_brok(b)
        self.show_logs()
        print(instance.logs_cache)
        self._assert_logs_queue(instance, [
            {'time': 1496341800.0,
             'message': 'SERVICE DOWNTIME ALERT: my-secured-elasticsearch-es2;check-es-http-alive;'
                        'STARTED; Service has entered a period of scheduled downtime',
             'plugin_output': ' Service has entered a period of scheduled downtime',
             'type': 'SERVICE DOWNTIME',
             'state': 'STARTED',
             'host_name': 'my-secured-elasticsearch-es2',
             'service_description': 'check-es-http-alive'}
        ])
        assert result is True

        # Host / service checks flapping
        # SERVICE FLAPPING ALERT: my-elasticsearch-es3;check-es-status;STARTED;
        # Service appears to have started flapping (101.0% change >= 50.0% threshold)
        b = Brok({'type': 'monitoring_log', 'data': {
            'level': 'info',
            'message': 'SERVICE FLAPPING ALERT: my-elasticsearch-es3;check-es-status;STARTED;'
                       'Service appears to have started flapping (101.0% change >= 50.0% threshold)'
        }})
        b.prepare()
        result = instance.manage_brok(b)
        self.show_logs()
        print(instance.logs_cache)
        self._assert_logs_queue(instance, [
            {'time': 1496341800.0,
             'message': 'SERVICE FLAPPING ALERT: my-elasticsearch-es3;check-es-status;STARTED;'
                        'Service appears to have started flapping (101.0% change >= 50.0% threshold)',
             'plugin_output': 'Service appears to have started flapping (101.0% change >= 50.0% threshold)',
             'type': 'SERVICE FLAPPING',
             'state': 'STARTED',
             'host_name': 'my-elasticsearch-es3',
             'service_description': 'check-es-status'}
        ])
        assert result is True

        b = Brok({'type': 'monitoring_log', 'data': {
            'level': 'info',
            'message': "ACTIVE SERVICE CHECK: localhost;Nrpe-status;OK;HARD;1;NRPE v2.15"
        }})
        b.prepare()
        result = instance.manage_brok(b)
        self.show_logs()
        print(instance.logs_cache)
        #
        #
        # Unhandled message!
        #
        #
        self._assert_logs_queue(instance, [])
        assert result is True

        b = Brok({'type': 'monitoring_log', 'data': {
            'level': 'info',
            'message': "PASSIVE SERVICE CHECK: localhost;nsca_uptime;0;OK: uptime: 02:38h, "
                       "boot: 2017-08-31 06:18:03 (UTC)|'uptime'=9508s;2100;90000"
        }})
        b.prepare()
        result = instance.manage_brok(b)
        self.show_logs()
        print(instance.logs_cache)
        #
        #
        # Unhandled message!
        #
        #
        self._assert_logs_queue(instance, [])
        assert result is True

        # Comments:
        # HOST COMMENT: docker_shinken;admin;Comment for this host
        # SERVICE COMMENT: docker_shinken;local_check_disk;admin;Comment for this service
        b = Brok({'type': 'monitoring_log', 'data': {
            'level': 'info',
            'message': "SERVICE COMMENT: docker_shinken;local_check_disk;admin;"
                       "Comment for this service"
        }})
        b.prepare()
        result = instance.manage_brok(b)
        self.show_logs()
        print(instance.logs_cache)
        self._assert_logs_queue(instance, [
            {'time': 1496341800.0,
             'message': 'SERVICE COMMENT: docker_shinken;local_check_disk;admin;'
                        'Comment for this service',
             'type': 'SERVICE COMMENT',
             'contact_name': 'admin',
             'plugin_output': 'Comment for this service',
             'host_name': 'docker_shinken',
             'service_description': 'local_check_disk'}
        ])
        assert result is True

        b = Brok({'type': 'monitoring_log', 'data': {
            'level': 'info',
            'message': "HOST COMMENT: docker_shinken;admin;Comment for this host"
        }})
        b.prepare()
        result = instance.manage_brok(b)
        self.show_logs()
        print(instance.logs_cache)
        self._assert_logs_queue(instance, [
            {'time': 1496341800.0,
             'message': 'HOST COMMENT: docker_shinken;admin;Comment for this host',
             'type': 'HOST COMMENT',
             'contact_name': 'admin',
             'plugin_output': 'Comment for this host',
             'host_name': 'docker_shinken',
             'service_description': ''}
        ])
        assert result is True

        b = Brok({'type': 'monitoring_log', 'data': {
            'level': 'info',
            'message': "HOST COMMENT: test;alignak;Host comment 2"
        }})
        b.prepare()
        result = instance.manage_brok(b)
        self.show_logs()
        print(instance.logs_cache)
        self._assert_logs_queue(instance, [
            {'time': 1496341800.0,
             'message': 'HOST COMMENT: test;alignak;Host comment 2',
             'type': 'HOST COMMENT',
             'contact_name': 'alignak',
             'plugin_output': 'Host comment 2',
             'host_name': 'test',
             'service_description': ''}
        ])
        assert result is True

        b = Brok({'type': 'monitoring_log', 'data': {
            'level': 'info',
            'message': "HOST COMMENT: test;alignak;Host comment 3"
        }})
        b.prepare()
        result = instance.manage_brok(b)
        self.show_logs()
        print(instance.logs_cache)
        self._assert_logs_queue(instance, [
            {'time': 1496341800.0,
             'message': 'HOST COMMENT: test;alignak;Host comment 3',
             'type': 'HOST COMMENT',
             'contact_name': 'alignak',
             'plugin_output': 'Host comment 3',
             'host_name': 'test',
             'service_description': ''}
        ])
        assert result is True
