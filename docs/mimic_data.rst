Mimicking the Data Stream
=========================

To mimic the data stream, minard comes with a script that will push a data file
produced by the data server when run with the option `--save-raw-data` over a
socket connection. To run it, you just need a raw data file, and then you can
push it over a socket on port 4000 (the default consumer port) by running the
following commands::

    $ source [path/to/virtual-env]/bin/activate
    $ data_server [path/to/data/run/file]
