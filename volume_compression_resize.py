#!/usr/bin/env python3

################################################################################
#
# This sample code pulls volume level compression savings for a given aggregate
# and gives a recommendation for increasing volume size.
#
# Setup Instructions:
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
# FlexGroup notes:
# 1. FlexGroups are likely to have constituent volumes moved at various times.
# 2. Recommendations are made to keep the FlexGroup no more than 90% full.
# 3. ONTAP will automatically try to keep all FlexGroup constituents at a
#    similar level of free space.
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
        description="Retrieve NetApp volume data and calculate recommended size increase."
    )
    parser.add_argument("-cluster", required=True, help="Cluster hostname or IP")
    parser.add_argument("-aggr", required=True, help="Aggregate name to filter volumes")
    parser.add_argument("-user", required=True, help="Username for authentication")
    parser.add_argument("-debug", action='store_true', required=False, help="Enable debug")
    parser.add_argument("-xml", action='store_true', required=False, help="Enable xml debug")
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
        available = volume.space.available
        used = volume.space.used

        # Calculate the required increase.
        recommended_increase = ceil(compression_saved / ((100-snapshot_percent)/100))

        # Debugging if required.
        if args.debug:
            print(f"DEBUG: {svm}:{vol_name} compression_saved:{compression_saved} snap_reserve:{snapshot_percent}")
            print(f"DEBUG: {svm}:{vol_name} Recommended Size Increase: {recommended_increase} bytes")
        if args.xml:
            print("START XML")
            pprint.pprint(volume.to_dict())
            print("END XML")

        # Print out FlexVol volume resize recommended command.
        if style == "flexvol" and compression_saved:
            print(f"volume size -vserver {svm} -volume {vol_name} -new-size +{recommended_increase}")

        # Perform calculations and print FlexGroup recommendations.
        if style == "flexgroup":
            available_gb = int(available / (1024*1024*1024))
            compression_saved_gb = ceil(compression_saved / (1024*1024*1024))
            afs_size = used + available
            used_wo_compression = used + compression_saved
            used_percent_wo_compression = int(100 * ((used_wo_compression) / afs_size))
            print(f"FlexGroup '{vol_name}' has {available_gb}GB available and {compression_saved_gb}GB saved by compression.")
            print(f"FlexGroup '{vol_name}' capacity utilization without compression savings would be {used_percent_wo_compression}%")
            if used_percent_wo_compression > 90:
                target_90_capacity = ceil((used_wo_compression / .9) - afs_size)
                target_90_capacity_gb = ceil(target_90_capacity / (1024*1024*1024))
                print(f"FlexGroup '{vol_name}' needs an extra {target_90_capacity_gb}GB to stay at 90% capacity without compression savings")

if __name__ == "__main__":
    main()
