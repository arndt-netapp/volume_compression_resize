volume_compression_resize.py

This sample code pulls volume level compression savings for a given aggregate
and gives a recommendation for increasing volume size.

```
Setup Instructions:
 
1. Create and activate a Python virtual environment:
  $ python3 -m venv netapp-env
  $ source netapp-env/bin/activate

2. Install the NetApp REST Python client:
  $ pip install netapp-ontap

3. Run the script with CLI options:
  $ volume_compression_resize.py -cluster <CLUSTER> -aggr <aggr> -user <USER>
                                 [-check] [-target <percentage>]
                                 [-debug] [-xml]

Examples:
1. Print out volume resize commands for all volumes to grow active filesystems
   the same amount as the current compression savings for each volume. This
   approach may be more useful before performing a volume move.
     volume_compression_resize.py -cluster cluster1 -aggr aggr1 -user admin
2. Print out volume resize commands for volumes that would be over 80% full
   without compression savings, resizing them to reach 80% full if all current
   compression savings were lost at the volume level.  This approach may be
   more useful after a volume move was performed without a resize.
     volume_compression_resize.py -cluster cluster1 -aggr aggr1 -user admin \
     -check -target 80

FlexGroup notes:
1. FlexGroups are likely to have constituent volumes moved at various times.
2. It is recommended to keep FlexGroups no more than 90% full.
3. ONTAP will automatically try to keep all FlexGroup constituents at a
   similar level of free space.
4. Extra detail is printed for FlexGroup volumes to aid in sizing decisions.
```

Using volume_compression_resize.py
```
usage: volume_compression_resize.py [-h] -cluster CLUSTER -aggr AGGR -user
                                    USER [-check] [-target TARGET] [-debug]
                                    [-xml]

Retrieve NetApp volume data and calculate recommended size increase.

optional arguments:
  -h, --help        show this help message and exit
  -cluster CLUSTER  Cluster hostname or IP
  -aggr AGGR        Aggregate name to filter volumes
  -user USER        Username for authentication
  -check            Only check for volumes that would be over 'target' full
                    percentage
  -target TARGET    Target volume full percentage (default: 90)
  -debug            Enable debug
  -xml              Enable xml debug
```
