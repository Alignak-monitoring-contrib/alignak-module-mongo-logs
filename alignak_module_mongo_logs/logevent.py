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
#
# This file incorporates work covered by the following copyright and
# permission notice:
#
#  Copyright (C) 2009-2014:
#     Thibault Cohen, titilambert@gmail.com
#     Grégory Starck, g.starck@gmail.com
#     aviau, alexandre.viau@savoirfairelinux.com
#     Sebastien Coavoux, s.coavoux@free.fr

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
"""
This module lists provide facilities to parse log type Broks.
The supported event are listed in the event_type variable
"""

import re

# pylint: disable=bad-continuation
EVENT_TYPE_PATTERN = re.compile(
    r'^\[[0-9]{10}] (TIMEPERIOD TRANSITION|EXTERNAL COMMAND|'
    r'RETENTION SAVE|RETENTION LOAD|'
    r'CURRENT HOST STATE|CURRENT SERVICE STATE|'
    r'HOST COMMENT|SERVICE COMMENT|'
    r'HOST NOTIFICATION|SERVICE NOTIFICATION|'
    r'HOST ALERT|SERVICE ALERT|'
    r'HOST EVENT HANDLER|SERVICE EVENT HANDLER|'
    r'ACTIVE HOST CHECK|ACTIVE SERVICE CHECK|'
    r'PASSIVE HOST CHECK|PASSIVE SERVICE CHECK|'
    r'HOST ACKNOWLEDGE ALERT|SERVICE ACKNOWLEDGE ALERT|'
    r'HOST DOWNTIME ALERT|SERVICE DOWNTIME ALERT|'
    r'HOST FLAPPING ALERT|SERVICE FLAPPING ALERT)($|: .*)'
)
EVENT_TYPES = {
    'TIMEPERIOD_TRANSITION': {
        # [1490998324] TIMEPERIOD TRANSITION: 24x7;-1;1
        'pattern': r'^\[([0-9]{10})] (TIMEPERIOD TRANSITION): (.*)',
        'properties': [
            'time',
            'type',     # 'TIMEPERIOD TRANSITION'
            'output',   # 'WARNING - load average: 5.04, 4.67, 5.04'
        ]
    },
    'RETENTION_LOAD': {
        # [1490998324] RETENTION LOAD: scheduler
        'pattern': r'^\[([0-9]{10})] (RETENTION LOAD): (.*)',
        'properties': [
            'time',
            'type',     # 'RETENTION LOAD'
            'output',   # 'scheduler name
        ]
    },
    'RETENTION_SAVE': {
        # [1490998324] RETENTION SAVE: scheduler
        'pattern': r'^\[([0-9]{10})] (RETENTION SAVE): (.*)',
        'properties': [
            'time',
            'type',     # 'RETENTION SAVE'
            'output',   # 'scheduler name
        ]
    },
    'EXTERNAL': {
        # [1490997636] EXTERNAL COMMAND: [1490997512]
        # PROCESS_HOST_CHECK_RESULT;ek3022sg-0001;0;EK3022SG-0001 is alive,
        # uptime is 43639 seconds (0 days 12 hours 7 minutes 19 seconds 229 ms)|'Uptime'=43639
        'pattern': r'^\[([0-9]{10})] (EXTERNAL COMMAND): '
                   r'([^\;]*);([^\;]*)',
        'properties': [
            'time',
            'event_type',  # 'EXTERNAL COMMAND'
            'command',  # 'PROCESS_SERVICE_CHECK_RESULT'
            'parameters',  # ;ek3022sg-0001;svc_Screensaver;0;Ok|'ScreensaverOff'=61c
        ]
    },
    'CURRENT_STATE': {
        # ex: "[1498108167] CURRENT HOST STATE: localhost;UP;HARD;1;Host assumed to be UP"
        # ex: "[1498108167] CURRENT SERVICE STATE: localhost;Maintenance;UNKNOWN;HARD;0;"
        'pattern': r'^\[([0-9]{10})] (CURRENT) (HOST|SERVICE) (STATE): '
                   r'([^\;]*);(?:([^\;]*);)?([^\;]*);([^\;]*);([^\;]*);([^\;]*)',
        'properties': [
            'time',
            'type',                 # 'CURRENT'
            'item_type',            # 'SERVICE' (or could be 'HOST')
            'type2',                # 'STATE'
            'host_name',            # 'localhost'
            'service_description',  # 'Maintenance' (or could be None)
            'state',                # 'UP'
            'state_type',           # 'HARD'
            'attempts',             # '0'
            'output',               # 'WARNING - load average: 5.04, 4.67, 5.04'
        ]
    },
    'ACTIVE_CHECK': {
        # ex: [1402515279] ACTIVE HOST CHECK: north_host_002;UP;1;I am always Up
        # ex: [1402515279] ACTIVE SERVICE CHECK: south_host_006;dummy_no_output;OK;1;
        # Service internal check result: 0
        'pattern': r'^\[([0-9]{10})] (ACTIVE) (HOST|SERVICE) (CHECK): '
                   r'([^\;]*);(?:([^\;]*);)?([^\;]*);([^\;]*);([^\;]*)',
        'properties': [
            'time',
            'type',                 # 'ACTIVE'
            'item_type',            # 'SERVICE' (or could be 'HOST')
            'type2',                # 'CHECK'
            'host_name',            # 'localhost'
            'service_description',  # 'cpu load maui' (or could be None)
            'state',                # 'WARNING'
            'attempts',             # '0'
            'output',               # 'NRPE v2.15'
        ]
    },
    'PASSIVE_CHECK': {
        # ex: "[1402515279] PASSIVE SERVICE CHECK: localhost;nsca_uptime;0;OK: uptime: 02:38h,
        # boot: 2017-08-31 06:18:03 (UTC)|'uptime'=9508s;2100;90000"
        'pattern': r'^\[([0-9]{10})] (PASSIVE) (HOST|SERVICE) (CHECK): '
                   r'([^\;]*);(?:([^\;]*);)?([^\;]*);([^$]*)',
        'properties': [
            'time',
            'type',                 # 'PASSIVE'
            'item_type',            # 'SERVICE' (or could be 'HOST')
            'type2',                # 'CHECK'
            'host_name',            # 'localhost'
            'service_description',  # 'nsca_uptime' (or could be None)
            'state_id',             # '0'
            'output',               # 'OK: uptime: 02:38h, boot: 2017-08-31 06:18:03 (UTC)
                                    # |'uptime'=9508s;2100;90000'
        ]
    },
    'NOTIFICATION': {
        # ex: "[1402515279] SERVICE NOTIFICATION:
        # admin;localhost;check-ssh;CRITICAL;notify-service-by-email;Connection refused"

        # HOST NOTIFICATION: notified;south_host_005;DOWN;1;
        #   notify-host-by-log;I am always Up but sometimes Down...

        # SERVICE NOTIFICATION: notified;north_host_001;dummy_critical;CRITICAL;1;
        #   notify-service-by-log;north_host_001-dummy_critical-2
        'pattern': r'\[([0-9]{10})\] (HOST|SERVICE) (NOTIFICATION): '
                   r'([^\;]*);([^\;]*);(?:([^\;]*);)?([^\;]*);([^\;]*);([^\;]*);([^\;]*)',
        'properties': [
            'time',
            'item_type',            # 'SERVICE' (or could be 'HOST')
            'type',                 # 'NOTIFICATION'
            'contact_name',         # 'admin'
            'host_name',            # 'localhost'
            'service_description',  # 'check-ssh' (or could be None)
            'state',                # 'CRITICAL'
            'notification_number',  # '1'
            'command_name',         # 'notify-service-by-email'
            'output',               # 'Connection refused'
        ]
    },
    'ALERT': {
        # ex: "[1329144231] SERVICE ALERT:
        #  dfw01-is02-006;cpu load maui;WARNING;HARD;4;WARNING - load average: 5.04, 4.67, 5.04"
        'pattern': r'^\[([0-9]{10})] (HOST|SERVICE) (ALERT): '
                   r'([^\;]*);(?:([^\;]*);)?([^\;]*);([^\;]*);([^\;]*);([^\;]*)',
        'properties': [
            'time',
            'item_type',            # 'SERVICE' (or could be 'HOST')
            'type',                 # 'ALERT'
            'host_name',            # 'localhost'
            'service_description',  # 'cpu load maui' (or could be None)
            'state',                # 'WARNING'
            'state_type',           # 'HARD'
            'attempts',             # '4'
            'output',               # 'WARNING - load average: 5.04, 4.67, 5.04'
        ]
    },
    'EVENT': {
        # ex: "[1329144231] HOST EVENT HANDLER: host-03;DOWN;HARD;0;g_host_event_handler"
        'pattern': r'^\[([0-9]{10})] (HOST|SERVICE) (EVENT HANDLER): '
                   r'([^\;]*);(?:([^\;]*);)?([^\;]*);([^\;]*);([^\;]*);([^\;]*)',
        'properties': [
            'time',
            'item_type',            # 'SERVICE' (or could be 'HOST')
            'type',                 # 'EVENT HANDLER'
            'host_name',            # 'localhost'
            'service_description',  # 'cpu load maui' (or could be None)
            'state',                # 'WARNING'
            'state_type',           # 'HARD'
            'attempts',             # '4'
            'output',               # 'g_host_event_handler'
        ]
    },
    'COMMENT': {
        # ex: "[1329144231] SERVICE COMMENT:
        #  dfw01-is02-006;cpu load maui;author;Comment text"
        'pattern': r'^\[([0-9]{10})] (HOST|SERVICE) (COMMENT): '
                   r'([^\;]*);(?:([^\;]*);)?([^\;]*);([^$]*)',
        'properties': [
            'time',
            'item_type',            # 'SERVICE' (or could be 'HOST')
            'type',                 # 'COMMENT'
            'host_name',            # 'localhost'
            'service_description',  # 'cpu load maui' (or could be None)
            'contact_name',
            'output',               # 'WARNING - load average: 5.04, 4.67, 5.04'
        ]
    },
    'ACKNOWLEDGE': {
        # ex: "[1279250211] HOST ACKNOWLEDGE STARTED:
        # maast64;Host has been acknowledged"
        'pattern': r'^\[([0-9]{10})] (HOST|SERVICE) (ACKNOWLEDGE) ALERT: '
                   r'([^\;]*);(?:([^\;]*);)?([^\;]*);([^\;]*)',
        'properties': [
            'time',
            'item_type',            # 'SERVICE' or 'HOST'
            'type',                 # 'ACKNOWLEDGE'
            'host_name',            # The hostname
            'service_description',  # The service description or None
            'state',                # 'STARTED' or 'EXPIRED'
            'output',               # 'Host has been acknowledged'
        ]
    },
    'DOWNTIME': {
        # ex: "[1279250211] HOST DOWNTIME ALERT:
        # maast64;STARTED; Host has entered a period of scheduled downtime"
        'pattern': r'^\[([0-9]{10})] (HOST|SERVICE) (DOWNTIME) ALERT: '
                   r'([^\;]*);(?:([^\;]*);)?([^\;]*);([^\;]*)',
        'properties': [
            'time',
            'item_type',            # 'SERVICE' or 'HOST'
            'type',                 # 'DOWNTIME'
            'host_name',            # The hostname
            'service_description',  # The service description or None
            'state',                # 'STOPPED' or 'STARTED'
            'output',               # Host has entered a period of scheduled downtime
        ]
    },
    'FLAPPING': {
        # service flapping ex: "[1375301662] SERVICE FLAPPING ALERT:
        # testhost;check_ssh;STARTED;
        # Service appears to have started flapping (24.2% change >= 20.0% threshold)"

        # host flapping ex: "[1375301662] HOST FLAPPING ALERT:
        # hostbw;STARTED; Host appears to have started flapping (20.1% change > 20.0% threshold)"
        'pattern': r'^\[([0-9]{10})] (HOST|SERVICE) (FLAPPING) ALERT: '
        r'([^\;]*);(?:([^\;]*);)?([^\;]*);([^\;]*)',
        'properties': [
            'time',
            'item_type',            # 'SERVICE' or 'HOST'
            'type',                 # 'FLAPPING'
            'host_name',            # The hostname
            'service_description',  # The service description or None
            'state',                # 'STOPPED' or 'STARTED'
            'output',               # 'Service appears to have started flapping ...
        ]
    }
}


class LogEvent(object):  # pylint: disable=too-few-public-methods, useless-object-inheritance
    """Class for parsing event logs
    Populates self.data with the log type's properties
    """

    def __init__(self, log):
        self.data = {}
        self.valid = False
        self.time = None
        # self.event_type = 'unknown'
        self.pattern = 'unknown'

        # Find the type of event
        event_type_match = EVENT_TYPE_PATTERN.match(log)
        if not event_type_match:
            return

        self.pattern = event_type_match.group(1)
        matched = self.pattern.split()
        # self.pattern = matched[0]
        if matched[0] in ['HOST', 'SERVICE']:
            self.pattern = matched[1]
        self.pattern = self.pattern.replace('HOST', '')
        self.pattern = self.pattern.replace('SERVICE', '')
        self.pattern = self.pattern.replace('  ', ' ')

        event_key = self.pattern.replace(' ', '_')
        if event_key not in EVENT_TYPES:
            return

        event_type = EVENT_TYPES[event_key]
        properties_match = re.match(event_type['pattern'], log)
        if not properties_match:
            return

        self.valid = True

        # Populate self.data with the event's properties
        for i, prop in enumerate(event_type['properties']):
            self.data[prop] = properties_match.group(i + 1)

        # Convert the time to int
        self.data['time'] = int(self.data['time'])

        # Convert some fields to int
        for field in ['attempts', 'notification_number', 'state_id']:
            if field in self.data:
                try:
                    self.data[field] = int(self.data[field])
                except ValueError:
                    self.data[field] = -1

        if 'item_type' in self.data:
            self.data['type'] = self.data['item_type'] + ' ' + self.data['type']
            if 'type2' in self.data:
                self.data['type'] = self.data['type'] + ' ' + self.data['type2']
                del self.data['type2']

    def __str__(self):
        return str(self.data)
