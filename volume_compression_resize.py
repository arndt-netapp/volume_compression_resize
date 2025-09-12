#!/usr/bin/env python3

################################################################################
#
# This sample code pulls flexvol level compression savings for a given aggregate
# and gives a recommendation for increasing volume size.
#
# Setup Instructions:
#
# 1. Create and activate a Python virtual environment:
#   $ python3 -m venv netapp-env
#   $ source netapp-env/bin/activate
#
# 2. Install the NetApp REST Python client:
#   $ pip install netapp-ontap
#
# 3. Run the script with CLI options:
#   $ volume_compression_resize.py -cluster <CLUSTER> -aggr <aggr> -user <USER>
#
################################################################################

import argparse
import getpass
import pprint
from math import ceil
from netapp_ontap import HostConnection, config
from netapp_ontap.resources import Volume

# Get CLI arguments.
def parse_args():
    parser = argparse.ArgumentParser(
        description="Retrieve NetApp flexvol data and calculate recommended size increases."
    )
    parser.add_argument("-cluster", required=True, help="Cluster hostname or IP")
    parser.add_argument("-aggr", required=True, help="Aggregate name to filter volumes")
    parser.add_argument("-user", required=True, help="Username for authentication")
    parser.add_argument("-debug", action='store_true', required=False, help="Enable debug")
    parser.add_argument("-details", action='store_true', required=False, help="Enable detaild debug")
    return parser.parse_args()

# Main.
def main():
    # Parse CLI and get password.
    args = parse_args()
    password = getpass.getpass("Enter password: ")

    # Setup the REST API connection to ONTAP.
    # Using verify=False to ignore that we may see self-signed SSL certificates.
    config.CONNECTION = HostConnection(
        host = args.cluster,
        username = args.user,
        password = password,
        verify = False,
        poll_timeout = 120,
    )

    # Get the volumes on the given aggregate.
    volume_args = {
        "aggregates.name" : args.aggr,
    }
    volumes = Volume.get_collection(**volume_args)

    # Iterate over the volumes and print the required size increase.
    for volume in volumes:
        # Gather volume attributes.
        volume.get(fields="name,svm.name,style,efficiency,space,aggregates")
        vol_name = volume.name
        svm = volume.svm.name
        style = volume.style
        compression_saved = volume.efficiency.space_savings.compression
        snapshot_percent = volume.space.snapshot.reserve_percent

        # Calculate the required increase.
        if style == "flexvol":
            recommended_increase = ceil(compression_saved / ((100-snapshot_percent)/100))

        # Debugging if required.
        if style == "flexvol" and args.debug:
            print(f"{svm}:{vol_name} {compression_saved} {snapshot_percent} Recommended Size Increase: {recommended_increase:.2f} bytes\n")
        if style == "flexvol" and args.details:
            pprint.pprint(volume.to_dict())

        # Print out volume resize command.
        if style == "flexvol" and compression_saved:
            print(f"volume size -vserver {svm} -volume {vol_name} -new-size +{recommended_increase}")

        # Print a warning for FlexGroups which may require special handling.
        if style == "flexgroup":
            print(f"volume '{vol_name}' is a FlexGroup! Perform manual resizing if required.")

if __name__ == "__main__":
    main()
