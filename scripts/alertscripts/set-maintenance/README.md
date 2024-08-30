# Set Maintenance

## Overview

[Zabbix maintenance periods](https://www.zabbix.com/documentation/current/manual/maintenance) are crucial for managing IT infrastructure monitoring. 
These periods allow temporarily suspending monitoring for specific hosts or host groups during maintenance, updates, or other scheduled activities. 
Such temporary exclusions prevent false alarms and notifications, enhancing the accuracy and efficiency of the monitoring system overall.

The `set_maintenance.py` script automates the creation of maintenance periods in Zabbix. 
It can set up a maintenance period for a specified host or for the smallest host group that the host belongs to. 
By automating this process, the script simplifies the management of monitoring downtime. 
The script provides flexibility by allowing execution either from the Zabbix interface or manually from the command line.

## Setup

1. Ensure that the `zabbix_api` library is available in your environment.

2. Prepare a configuration file with the necessary variables.

3. Make sure the script is properly configured to read the configuration file and execute with the correct parameters.

## Zabbix configuration

No specific Zabbix configuration is required.

## Usage

The script can be executed from the Zabbix interface or directly from the command line.

To run the script manually, use the following command:

```
/path/to/set_maintenance.py <CONFIG_FILE> <HOST> [OPTIONS]
```

- `<CONFIG_FILE>`: The path to the configuration file containing Zabbix server URL and [API token](https://www.zabbix.com/documentation/current/en/manual/web_interface/frontend_sections/users/api_tokens). The file should be in `.ini` format with a section `[zabbix]` for these variables:
  - `SERVER`: The URL of your Zabbix server, including the correct protocol (`http` or `https`)
  - `TOKEN_AUTH`: Your Zabbix API token
- `<HOST>`: The technical name of the host for which the maintenance period is being created

**Options:**

- `--period <SECONDS>`: Sets the duration of the maintenance period in seconds. This option is optional; if not provided, the default value is 3600 seconds (1 hour)
- `--no-data-collection`: If this option is specified, the maintenance period will be created without data collection. By default, data collection is enabled
- `--hostgroup`: When included, the script creates a maintenance period for the smallest host group that the specified host belongs to. If not specified, the maintenance period will be created only for the given host
- `--user <USERNAME>`: Specifies the username to be included in the description of the maintenance period. If not provided, `unknown user` will be used by default

Make sure to adjust the script path and configuration file path according to your environment.

## Acknowledgments

- [Zabbix API Method reference](https://www.zabbix.com/documentation/current/en/manual/api/reference)
