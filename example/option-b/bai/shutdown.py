import os
from dask_gateway import Gateway

gateway = Gateway()

cluster = gateway.connect(os.environ["DASK_GATEWAY_CLUSTER"])

cluster.shutdown()