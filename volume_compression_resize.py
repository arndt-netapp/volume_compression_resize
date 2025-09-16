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
#                                  [-target <percentage>] [-check]
#                                  [-debug] [-xml]
#
# Examples:
# 1. Print out volume resize commands for all volumes to grow active filesystems
#    the same amount as the current compression savings for each volume. This
#    approach may be more useful before performing a volume move.
#      volume_compression_resize.py -cluster cluster1 -aggr aggr1 -user admin
# 2. Print out volume resize commands for volumes that would be over 80% full
#    without compression savings, resizing them to reach 80% full if all current
#    compression savings were lost at the volume level.  This approach may be
#    more useful after a volume move was performed without a resize.
#      volume_compression_resize.py -cluster cluster1 -aggr aggr1 -user admin \
#      -check -target 80
#
# FlexGroup notes:
# 1. FlexGroups are likely to have constituent volumes moved at various times.
# 2. It is recommended to keep FlexGroups no more than 90% full.
# 3. ONTAP will automatically try to keep all FlexGroup constituents at a
#    similar level of free space.
# 4. Extra detail is printed for FlexGroup volumes to aid in sizing decisions.
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
        description="Retrieve NetApp volume data and calculate recommended size increases."
    )
    parser.add_argument("-cluster", required=True, help="Cluster hostname or IP")
    parser.add_argument("-aggr", required=True, help="Aggregate name to filter volumes")
    parser.add_argument("-user", required=True, help="Username for authentication")
    parser.add_argument("-check", action='store_true', required=False, help="Only check for volumes that would be over 'target' full percentage")
    parser.add_argument("-target", required=False, type=int, default='90', help="Target volume full percentage (default: 90)")
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
        used = volume.space.used
        available = volume.space.available

        # Perform the required calculations.
        recommended_increase = ceil(compression_saved / ((100-snapshot_percent)/100))
        afs_size = used + available
        used_wo_compression = used + compression_saved
        used_percent_wo_compression = int(100 * ((used_wo_compression) / afs_size))
        available_gb = int(available / (1024*1024*1024))
        compression_saved_gb = ceil(compression_saved / (1024*1024*1024))

        # Debugging if required.
        if args.debug:
            print(f"DEBUG: {svm}:{vol_name} compression_saved:{compression_saved} snap_reserve:{snapshot_percent}.")
            print(f"DEBUG: {svm}:{vol_name} style:{style} used:{used} available:{available}.")
            print(f"DEBUG: {svm}:{vol_name} Recommended Size Increase: {recommended_increase} bytes.")
        if args.xml:
            print("START XML")
            pprint.pprint(volume.to_dict())
            print("END XML")

        # Print out the volume resize recommended command as required.
        if compression_saved:
            # Print out extra information for FlexGroup volumes.
            if style == "flexgroup":
                print(f"INFO: FlexGroup '{vol_name}' has {available_gb}GB available and {compression_saved_gb}GB saved by compression.")
                print(f"INFO: FlexGroup '{vol_name}' capacity utilization without compression savings would be {used_percent_wo_compression}%.")
            if args.check and used_percent_wo_compression > args.target:
                target_capacity = ceil((used_wo_compression / (args.target/100)) - afs_size)
                target_capacity_gb = ceil(target_capacity / (1024*1024*1024))
                print(f"INFO: '{vol_name}' needs an extra {target_capacity_gb}GB to stay at {args.target}% capacity without compression savings.")
                print(f"volume size -vserver {svm} -volume {vol_name} -new-size +{target_capacity_gb}g")
            if not args.check:
                if style == "flexgroup":
                    print(f"INFO: Potential FlexGroup resize command: volume size -vserver {svm} -volume {vol_name} -new-size +{recommended_increase}")
                else:
                    print(f"volume size -vserver {svm} -volume {vol_name} -new-size +{recommended_increase}")

if __name__ == "__main__":
    main()
