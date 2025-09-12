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
```

Using volume_compression_resize.py
```
usage: volume_compression_resize.py [-h] -cluster CLUSTER -aggr AGGR -user USER [-debug]

Retrieve NetApp volume data and calculate recommended size increases.

options:
  -h, --help        show this help message and exit
  -cluster CLUSTER  Cluster hostname or IP
  -aggr AGGR        Aggregate name to filter volumes
  -user USER        Username for authentication
  -debug            Enable debug
```
