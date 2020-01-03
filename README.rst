Alignak Log MongoDB Module
==========================

**Note** that this module is only useful to get the Alignak monitoring logs in a Mongo DB if you do not use the Alignak backend

-----

*Alignak module for the monitoring logs*

.. image:: https://travis-ci.org/Alignak-monitoring-contrib/alignak-module-mongo-logs.svg?branch=develop
    :target: https://travis-ci.org/Alignak-monitoring-contrib/alignak-module-mongo-logs
    :alt: Develop branch build status

.. image:: https://landscape.io/github/Alignak-monitoring-contrib/alignak-module-mongo-logs/develop/landscape.svg?style=flat
    :target: https://landscape.io/github/Alignak-monitoring-contrib/alignak-module-mongo-logs/develop
    :alt: Development code static analysis

.. image:: https://codecov.io/gh/Alignak-monitoring-contrib/alignak-module-mongo-logs/branch/develop/graph/badge.svg
    :target: https://codecov.io/gh/Alignak-monitoring-contrib/alignak-module-mongo-logs
    :alt: Development code tests coverage

.. image:: https://badge.fury.io/py/alignak_module_mongo_logs.svg
    :target: https://badge.fury.io/py/alignak-module-mongo-logs
    :alt: Most recent PyPi version

.. image:: https://img.shields.io/badge/License-AGPL%20v3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0
    :alt: License AGPL v3

Installation
------------

The installation of this module will copy some configuration files in the Alignak default configuration directory (eg. */usr/local/etc/alignak*). The copied files are located in the default sub-directory used for the modules (eg. *arbiter/modules*).

From PyPI
~~~~~~~~~
To install the module from PyPI:
::

   sudo pip install alignak-module-mongo-logs


From source files
~~~~~~~~~~~~~~~~~
To install the module from the source files (for developing purpose):
::

   git clone https://github.com/Alignak-monitoring-contrib/alignak-module-mongo-logs
   cd alignak-module-mongo-logs
   sudo pip install . -e


Short description
-----------------

This module for Alignak collects the monitoring logs (alerts, notifications, ...) to log them into a collection of a Mongo DB.

This module was back-ported from the Shinken `mod-mongo-logs` but it does not manage the availability for hosts and services.

Configuration
-------------

Once installed, this module has its own configuration file in the */usr/local/etc/alignak/arbiter/modules* directory.
The default configuration file is *mod-mongo-logs.cfg*. This file is commented to help configure all the parameters.

To configure Alignak broker to use this module:

- edit your broker daemon configuration file
- add the `module_alias` parameter value (`logs`) to the `modules` parameter of the daemon

To configure this module for Mongo DB:

- edit the module configuration file to set the MongoDB parameters

Metrics
-------

This module is able to push metrics to an external TSDB (Graphite, InfluxDB). Configure the metrics parameters in the configuration:
::

   ; --------------------------------------------------------------------
   ; Module internal metrics
   ; Export module metrics to a statsd server.
   ; By default at localhost:8125 (UDP) with the alignak prefix
   ; Default is not enabled
   ; --------------------------------------------------------------------
   ;statsd_host = localhost
   ; For StatsD
   ;statsd_port = 8125
   ; For Graphite
   ;statsd_port = 2004
   ; Default
   ;statsd_prefix=alignak
   ; Use this prefix to use the alignak name in the metrics hierarchy
   ;statsd_prefix=%(alignak_name)s.modules
   ; Default is disabled
   ;statsd_enabled = 0
   ;graphite_enabled = 0
   ; --------------------------------------------------------------------


Available metrics:

- `committed-logs` counts the DB commited logs
- `monitoring-event-got.%s` counts the detected events
- `monitoring-event-ignored.%s` counts the ignored events (not DB commited)
- `queue-size` is the module message queue size. If greater than 1, it indicates a module overload because the queue should be emptied on each loop turn
- `managed-broks-time` is the broks management duration on each loop turn

**Note** that only the events in this list are DB commited: ['TIMEPERIOD TRANSITION', 'RETENTION LOAD', 'RETENTION SAVE', 'CURRENT STATE', 'NOTIFICATION', 'ALERT', 'DOWNTIME', 'FLAPPING', 'ACTIVE CHECK', 'PASSIVE CHECK', 'COMMENT', 'ACKNOWLEDGE', 'DOWNTIME']

An example Grafana dashboard:

.. image:: ./doc/_static/images/grafana.png
   :scale: 90 %



Bugs, issues and contributing
-----------------------------

Contributions to this project are welcome and encouraged ... `issues in the project repository <https://github.com/alignak-monitoring-contrib/alignak-module-mongo-logs/issues>`_ are the common way to raise an information.
