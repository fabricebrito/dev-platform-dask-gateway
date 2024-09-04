import os
from dask_gateway import Gateway

gateway = Gateway()

cluster = gateway.new_cluster(shutdown_on_close=False)
cluster.scale(4)

# save the cluster name to a file
with open("dask_cluster_name.txt", "w") as f:
    f.write(cluster.name)