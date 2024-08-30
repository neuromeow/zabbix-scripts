#!/usr/bin/env python3
"""Creates a new maintenance period with specified time period for the given host or for an entire host group.

You can see the script and additional details on GitHub:
https://github.com/neuromeow/zabbix-scripts/tree/master/scripts/alertscripts/set-maintenance

Usage:
    This script is supposed to be called from Scripts in Zabbix interface.

Manual usage:
    It is also possible to use independently, use --help or -h to see help.

Configuration:
    Ensure the `zabbix_maintenance.ini` file with the necessary variables is located on the Zabbix server.

    To use this script from the Zabbix interface, create a Zabbix Script object with settings similar to the following example:
        Name:
            Set maintenance for the host for 1d
        Scope:
            Manual host action
        Type:
            Script
        Execute on:
            Zabbix server
        Commands:
            /usr/lib/zabbix/alertscripts/set_maintenance.py /usr/lib/zabbix/alertscripts/zabbix_maintenance.ini "{HOST.HOST}" --period 86400 --user "{USER.USERNAME}"
        Host group:
            All
        User group:
            All

    You can specify one or more host groups and user groups as needed. It is recommended to create a dedicated user group for users who need access to this script.
    Ensure users have the "Execute scripts" permission (refer to User roles).

Notice:
    A maintenance period will not be created if a maintenance period with the same name already exists. The name is generated based on the host or host group and the script's execution time.
"""

import argparse
from configparser import ConfigParser
from datetime import datetime
import logging
import time

from zabbix_api import ZabbixAPI


def suspend_logging(func):
    """Suspends logging below warning level cause of ZabbixAPI."""
    def wrapper(*args, **kwargs):
        logging.disable(logging.INFO)
        try:
            return func(*args, **kwargs)
        finally:
            logging.disable(logging.NOTSET)
    return wrapper


@suspend_logging
def create_zabbix_authentication(zabbix_server, zabbix_token_auth):
    """Authenticates to Zabbix using an API token."""
    zabbix_authentication = ZabbixAPI(server=zabbix_server, timeout=30)
    zabbix_authentication.login(api_token=zabbix_token_auth)
    return zabbix_authentication


@suspend_logging
def get_host_host_id(zabbix_authentication, host_host):
    """Gets the ID of the given host by its technical name."""
    host = zabbix_authentication.host.get({'filter': {'host': [host_host]}})
    host_host_id = host[0]['hostid']
    return host_host_id


@suspend_logging
def get_host_hostgroups_names(zabbix_authentication, host_host_id):
    """Gets the host groups names of the given host by its id."""
    host_hostgroups = zabbix_authentication.hostgroup.get({'output': ['name'], 'hostids': host_host_id})
    host_hostgroups_names = [host_hostgroup['name'] for host_hostgroup in host_hostgroups]
    return host_hostgroups_names


@suspend_logging
def find_smallest_host_hostgroup(zabbix_authentication, host_hostgroups_names):
    """Finds the host group with the fewest number of hosts among the given host groups names."""
    smallest_host_hostgroup = None
    hostgroup_hosts_count_min = None
    for host_hostgroup_name in host_hostgroups_names:
        host_hostgroup = zabbix_authentication.hostgroup.get({
            'output': ['groupid', 'name'],
            'filter': {'name': host_hostgroup_name},
            'selectHosts': ['hostid']
        })
        if host_hostgroup:
            hostgroup_hosts_count = len(host_hostgroup[0]['hosts'])
            if hostgroup_hosts_count_min is None or hostgroup_hosts_count < hostgroup_hosts_count_min:
                hostgroup_hosts_count_min = hostgroup_hosts_count
                smallest_host_hostgroup = {
                    'hostgroup_groupid': host_hostgroup[0]['groupid'],
                    'hostgroup_name': host_hostgroup[0]['name']
                }
    return smallest_host_hostgroup


def create_maintenance_time_params(period, is_data_collection, user):
    """Returns a part of the parameters necessary for the Zabbix API method allows to create a maintenance period."""
    active_since = int(time.time())
    active_till = active_since + period
    maintenance_type = int(is_data_collection)
    description = f"The maintenance period was created using the script by {user}."
    maintenance_common_params = {
        'active_since': active_since,
        'active_till': active_till,
        'timeperiods': [{'period': period}],
        'maintenance_type': maintenance_type,
        'description': description,
    }
    return maintenance_common_params


@suspend_logging
def create_maintenance_for_host(zabbix_authentication, maintenance_common_params, host_host, host_id):
    """Creates a new maintenance period for the given host."""
    formatted_active_since = datetime.fromtimestamp(maintenance_common_params['active_since']).strftime("%Y-%m-%d %H:%M")
    name = f"Maintenance period for the host {host_host} since {formatted_active_since}"
    maintenance_common_params['name'] = name
    maintenance_common_params['hosts'] = [{'hostid': host_id}]
    zabbix_authentication.maintenance.create(maintenance_common_params)


@suspend_logging
def create_maintenance_for_hostgroup(zabbix_authentication, maintenance_common_params, hostgroup_name, hostgroup_groupid):
    """Creates a new maintenance period for the given host group."""
    formatted_active_since = datetime.fromtimestamp(maintenance_common_params['active_since']).strftime("%Y-%m-%d %H:%M")
    name = f"Maintenance period for the hostgroup {hostgroup_name} since {formatted_active_since}"
    maintenance_common_params['name'] = name
    maintenance_common_params['groups'] = [{'groupid': hostgroup_groupid}]
    zabbix_authentication.maintenance.create(maintenance_common_params)


def main():
    """Execute the main logic of the script."""
    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s",
                        level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")
    parser = argparse.ArgumentParser()
    parser.add_argument("credentials_file", help="configuration file with necessary variables for Zabbix")
    parser.add_argument("host", help="technical name of the host")
    parser.add_argument("--period", type=int, default=3600, help="duration of the maintenance period in seconds")
    parser.add_argument("--no-data-collection", action="store_true", dest="is_data_collection", help="without data collection")
    parser.add_argument("--hostgroup", action="store_true", help="create a maintenance period for the entire and smallest host group to which the host belongs")
    parser.add_argument("--user", default="unknown user", help="user name added to the description")
    args = parser.parse_args()
    config = ConfigParser()
    config.read(args.credentials_file)
    zabbix_server = config.get('zabbix', 'SERVER')
    zabbix_token_auth = config.get('zabbix', 'TOKEN_AUTH')
    zabbix_authentication = create_zabbix_authentication(zabbix_server, zabbix_token_auth)
    maintenance_time_params = create_maintenance_time_params(args.period, args.is_data_collection, args.user)
    host_host_id = get_host_host_id(zabbix_authentication, args.host)
    if args.hostgroup:
        host_hostgroups_names = get_host_hostgroups_names(zabbix_authentication, host_host_id)
        smallest_host_hostgroup = find_smallest_host_hostgroup(zabbix_authentication, host_hostgroups_names)
        try:
            create_maintenance_for_hostgroup(zabbix_authentication, maintenance_time_params, **smallest_host_hostgroup)
            logging.info("The maintenance period for the host group %s was successfully created.", smallest_host_hostgroup['hostgroup_name'])
        except Exception as err:
            logging.error("Failed to create the maintenance period for the host group %s. Error: %s", smallest_host_hostgroup['hostgroup_name'], err)
    else:
        try:
            create_maintenance_for_host(zabbix_authentication, maintenance_time_params, args.host, host_host_id)
            logging.info("The maintenance period for the host %s was successfully created.", args.host)
        except Exception as err:
            logging.error("Failed to create the maintenance period for the host %s. Error: %s", args.host, err)


if __name__ == "__main__":
    main()
