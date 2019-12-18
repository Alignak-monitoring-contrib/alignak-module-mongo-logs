#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (C) 2015-2015: Alignak team, see AUTHORS.txt file for contributors
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
#
# This file incorporates work covered by the following copyright and
# permission notice:
#
#  Copyright (C) 2014 - Savoir-Faire Linux inc.
#

#  This file is part of Shinken.
#
#  Shinken is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Shinken is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

import os

from alignak_test import AlignakTest
from alignak_module_mongo_logs.logevent import LogEvent


class TestParseLogEvent(AlignakTest):

    def test_from_file(self):
        self.maxDiff = None

        count_events = 0
        count_non_events = 0
        logs_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "./logs")
        print("Logs directory: %s" % logs_dir)
        for file in os.listdir(logs_dir):
            print("Log file: %s" % os.path.join(logs_dir, file))
            with open(os.path.join(logs_dir, file), "r") as logfile:
                data = logfile.readlines()
                for log in data:
                    log.rstrip()
                    log = log.replace('INFO: ', '')
                    log = log.replace('WARNING: ', '')
                    log = log.replace('ERROR: ', '')
                    print("Log: %s" % log)
                    event = LogEvent(log)
                    if not event.valid:
                        if 'RETENTION' not in log:
                            count_non_events += 1
                            print("*** Log (unparsed): %s" % log)
                    else:
                        count_events += 1
                        # print("Event: %s" % event)
        assert count_events > 0
        # assert count_non_events == 0

    def test_comment_service(self):
        self.maxDiff = None

        log = '[1402515279] SERVICE COMMENT: pi2;load;alignak;Service comment'
        expected = {
            'time': 1402515279, 'item_type': 'SERVICE', 'type': 'SERVICE COMMENT',
            'host_name': 'pi2', 'service_description': 'load', 'contact_name': 'alignak',
            'output': 'Service comment'
        }
        event = LogEvent(log)
        assert event.data == expected

    def test_comment_host(self):
        self.maxDiff = None

        log = '[1402515279] HOST COMMENT: pi2;alignak;Host comment'
        expected = {
            'time': 1402515279, 'item_type': 'HOST', 'type': 'HOST COMMENT', 'host_name': 'pi2',
            'service_description': None, 'contact_name': 'alignak', 'output': 'Host comment'
        }
        event = LogEvent(log)
        assert event.data == expected

    def test_ack_service(self):
        self.maxDiff = None

        log = '[1402515279] SERVICE ACKNOWLEDGE ALERT: pi2;load;STARTED;' \
              'Service problem has been acknowledged'
        expected = {
            'time': 1402515279, 'item_type': 'SERVICE', 'type': 'SERVICE ACKNOWLEDGE',
            'host_name': 'pi2', 'service_description': 'load', 'state': 'STARTED',
            'output': 'Service problem has been acknowledged'
        }
        event = LogEvent(log)
        assert event.data == expected

    def test_ack_host(self):
        self.maxDiff = None

        log = '[1402515279] HOST ACKNOWLEDGE ALERT: pi2;STARTED;Host problem has been acknowledged'
        expected = {
            'time': 1402515279, 'item_type': 'HOST', 'type': 'HOST ACKNOWLEDGE', 'host_name': 'pi2',
            'service_description': None, 'state': 'STARTED',
            'output': 'Host problem has been acknowledged'
        }
        event = LogEvent(log)
        assert event.data == expected

    def test_notification_service(self):
        log = '[1402515279] SERVICE NOTIFICATION: notified;north_host_001;dummy_critical;' \
              'CRITICAL;1;notify-service-by-log;north_host_001-dummy_critical-2 failed'
        expected = {
            'time': 1402515279, 'item_type': 'SERVICE', 'type': 'SERVICE NOTIFICATION',
            'contact_name': 'notified', 'host_name': 'north_host_001',
            'service_description': 'dummy_critical', 'state': 'CRITICAL', 'notification_number': 1,
            'command_name': 'notify-service-by-log',
            'output': 'north_host_001-dummy_critical-2 failed'
        }
        event = LogEvent(log)
        assert event.data == expected
        assert event.valid is True

    def test_notification_host(self):
        log = '[1402515279] HOST NOTIFICATION: notified;south_host_005;DOWN;1;' \
              'notify-host-by-log;I am always Up but sometimes Down...'
        expected = {
            'time': 1402515279, 'item_type': 'HOST', 'type': 'HOST NOTIFICATION',
            'contact_name': 'notified', 'host_name': 'south_host_005', 'service_description': None,
            'state': 'DOWN', 'notification_number': 1, 'command_name': 'notify-host-by-log',
            'output': 'I am always Up but sometimes Down...'
        }
        event = LogEvent(log)
        assert event.data == expected

    def test_alert_service(self):
        log = '[1329144231] SERVICE ALERT: south_host_000;dummy_random;UNREACHABLE;HARD;3;' \
              'Service internal check result: 4'
        expected = {
            'time': 1329144231, 'item_type': 'SERVICE', 'type': 'SERVICE ALERT',
            'host_name': 'south_host_000', 'service_description': 'dummy_random',
            'state': 'UNREACHABLE', 'state_type': 'HARD', 'attempts': 3,
            'output': 'Service internal check result: 4'
        }
        event = LogEvent(log)
        assert event.data == expected

    def test_alert_host(self):
        log = '[1329144231] HOST ALERT: south_host_003;DOWN;SOFT;2;' \
              'I am always Up but sometimes Down...'
        expected = {
            'time': 1329144231, 'item_type': 'HOST', 'type': 'HOST ALERT',
            'host_name': 'south_host_003', 'service_description': None, 'state': 'DOWN',
            'state_type': 'SOFT', 'attempts': 2, 'output': 'I am always Up but sometimes Down...'        }
        event = LogEvent(log)
        assert event.data == expected

    def test_event_handler_service(self):
        log = '[1329144231] SERVICE EVENT HANDLER: host-01;Output-Load;OK;HARD;0;' \
              'g_service_event_handler'
        expected = {
            'time': 1329144231, 'item_type': 'SERVICE', 'type': 'SERVICE EVENT HANDLER',
            'host_name': 'host-01', 'service_description': 'Output-Load', 'state': 'OK',
            'state_type': 'HARD', 'attempts': 0, 'output': 'g_service_event_handler'
        }
        event = LogEvent(log)
        assert event.data == expected

    def test_event_handler_host(self):
        log = '[1329144231] HOST EVENT HANDLER: host-01;DOWN;HARD;0;g_host_event_handler'
        expected = {
            'time': 1329144231, 'item_type': 'HOST', 'type': 'HOST EVENT HANDLER',
            'host_name': 'host-01', 'service_description': None, 'state': 'DOWN',
            'state_type': 'HARD', 'attempts': 0, 'output': 'g_host_event_handler'
        }
        event = LogEvent(log)
        assert event.data == expected

    def test_downtime_alert_host(self):
        log = '[1279250211] HOST DOWNTIME ALERT: testhost;STARTED; Host has entered a period of scheduled downtime'
        expected = {
            'time': 1279250211, 'item_type': 'HOST', 'type': 'HOST DOWNTIME',
            'host_name': 'testhost', 'service_description': None, 'state': 'STARTED',
            'output': ' Host has entered a period of scheduled downtime'
        }
        event = LogEvent(log)
        assert event.data == expected

    def test_downtime_alert_service(self):
        log = '[1279250211] SERVICE DOWNTIME ALERT: testhost;check_ssh;STARTED; ' \
              'Service has entered a period of scheduled downtime'
        expected = {
            'time': 1279250211, 'item_type': 'SERVICE', 'type': 'SERVICE DOWNTIME',
            'host_name': 'testhost', 'service_description': 'check_ssh', 'state': 'STARTED',
            'output': ' Service has entered a period of scheduled downtime'
        }
        event = LogEvent(log)
        assert event.data == expected

    def test_retention(self):
        log = '[1498111760] RETENTION SAVE: scheduler-master'
        expected = {
            'time': 1498111760, 'type': 'RETENTION SAVE', 'output': 'scheduler-master'
        }
        event = LogEvent(log)
        assert event.data == expected

        log = '[1498111760] RETENTION LOAD: scheduler-master'
        expected = {
            'time': 1498111760, 'type': 'RETENTION LOAD', 'output': 'scheduler-master'
        }
        event = LogEvent(log)
        print(event)
        assert event.data == expected

    def test_host_current_state(self):
        log = '[1498108167] CURRENT HOST STATE: localhost;UP;HARD;1;Host assumed to be UP'
        expected = {
            'time': 1498108167, 'type': 'HOST CURRENT STATE', 'item_type': 'HOST',
            'host_name': 'localhost', 'service_description': None, 'state': 'UP',
            'state_type': 'HARD', 'attempts': 1, 'output': 'Host assumed to be UP'
        }
        event = LogEvent(log)
        assert event.data == expected

    def test_service_current_state(self):
        log = '[1498108167] CURRENT SERVICE STATE: localhost;Maintenance;UNKNOWN;HARD;0;'
        expected = {
            'time': 1498108167, 'type': 'SERVICE CURRENT STATE', 'item_type': 'SERVICE',
            'host_name': 'localhost', 'service_description': 'Maintenance', 'state': 'UNKNOWN',
            'state_type': 'HARD', 'attempts': 0, 'output': ''
        }
        event = LogEvent(log)
        assert event.data == expected

    def test_active_check(self):
        log = '[1498108167] ACTIVE HOST CHECK: my-mongo-primary;UP;1;Host assumed to be UP'
        expected = {
            'time': 1498108167, 'type': 'HOST ACTIVE CHECK', 'item_type': 'HOST',
            'host_name': 'my-mongo-primary', 'service_description': None, 'state': 'UP',
            'attempts': 1, 'output': 'Host assumed to be UP'
        }
        event = LogEvent(log)
        assert event.data == expected

        log = '[1498108167] ACTIVE SERVICE CHECK: docker_shinken;local_check_disk_inode_root;OK;' \
              '1;DISK OK - free space: / 2213 MB (5% inode=64%);'
        expected = {
            'time': 1498108167, 'type': 'SERVICE ACTIVE CHECK', 'item_type': 'SERVICE',
            'host_name': 'docker_shinken', 'service_description': 'local_check_disk_inode_root',
            'state': 'OK', 'attempts': 1, 'output': 'DISK OK - free space: / 2213 MB (5% inode=64%)'
        }
        event = LogEvent(log)
        assert event.data == expected

    def test_passive_check(self):
        log = "[1498108167] PASSIVE HOST CHECK: localhost;0;Host is alive, uptime is 2291 seconds " \
              "(0 days 0 hours 38 minutes 11 seconds 215 ms)|'Uptime'=2291"
        expected = {
            'time': 1498108167, 'type': 'HOST PASSIVE CHECK', 'item_type': 'HOST',
            'host_name': 'localhost', 'service_description': None, 'state_id': 0,
            'output': "Host is alive, uptime is 2291 seconds (0 days 0 hours 38 minutes "
                      "11 seconds 215 ms)|'Uptime'=2291"
        }
        event = LogEvent(log)
        assert event.data == expected

        log = "[1498108167] PASSIVE SERVICE CHECK: localhost;nsca_uptime;0;OK: uptime: 02:38h, " \
              "boot: 2017-08-31 06:18:03 (UTC)|'uptime'=9508s;2100;90000"
        expected = {
            'time': 1498108167, 'type': 'SERVICE PASSIVE CHECK', 'item_type': 'SERVICE',
            'host_name': 'localhost', 'service_description': 'nsca_uptime', 'state_id': 0,
            'output': "OK: uptime: 02:38h, boot: 2017-08-31 06:18:03 (UTC)|'uptime'=9508s;2100;90000"
        }
        event = LogEvent(log)
        assert event.data == expected

    def test_host_flapping(self):
        log = '[1375301662] HOST FLAPPING ALERT: hostbw;STARTED; Host appears to have ' \
              'started flapping (20.1% change > 20.0% threshold)'
        expected = {
            'time': 1375301662, 'item_type': 'HOST', 'type': 'HOST FLAPPING', 'host_name': 'hostbw',
            'service_description': None, 'state': 'STARTED',
            'output': ' Host appears to have started flapping (20.1% change > 20.0% threshold)'
        }
        event = LogEvent(log)
        assert event.data == expected

    def test_service_flapping(self):
        log = '[1375301662] SERVICE FLAPPING ALERT: testhost;check_ssh;STARTED; Service appears ' \
              'to have started flapping (24.2% change >= 20.0% threshold)'
        expected = {
            'time': 1375301662, 'item_type': 'SERVICE', 'type': 'SERVICE FLAPPING',
            'host_name': 'testhost', 'service_description': 'check_ssh', 'state': 'STARTED',
            'output': ' Service appears to have started flapping (24.2% change >= 20.0% threshold)'
        }
        event = LogEvent(log)
        assert event.data == expected
