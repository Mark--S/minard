Data Sources
============

Dispatch Stream
---------------

The dispatch stream is processed by the `minard_dispatch
<https://github.com/snoplus/minard/blob/master/bin/minard_dispatch>`_
script and written to the redis database.

To run the dispatch processor as a daemon::

    $ source [/path/to/virtual-env]/bin/activate
    $ minard_dispatch --host [dispatcher ip]

To see how to set up a local dispatcher see :doc:`dispatch_local`.

Data Stream
-----------

The data stream is processed directly from a socket connection to the data
server. The stream is processed by two scripts:

`data_producer
<https://github.com/snoplus/minard/blob/master/bin/data_producer>`_
    This script receives the raw data from the data stream server and pushes it
    to different sockets depending on the type of data. Currently it sends CMOS
    packets to port 5557 and base current packets to port 5558.

`data_consumer
<https://github.com/snoplus/minard/blob/master/bin/data_consumer>`_
    This script processes the data packets pushed by the `data_producer
    <https://github.com/snoplus/minard/blob/master/bin/data_producer>`_ script.

For more information on the data file formats see `Data File Format
<http://snopl.us/detector/html/daq.html>`_.

To mimic the data stream see :doc:`mimic_data`.

