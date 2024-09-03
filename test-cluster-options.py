from dask_gateway import Gateway
from time import sleep
import os
# Connect to the Dask Gateway
gateway = Gateway(os.environ['DASK_GATEWAY_URL'])

# Define cluster options with a custom worker container image
cluster_options = gateway.cluster_options()

print(cluster_options)
cluster_options['image'] = os.environ['DASK_WORKER_IMAGE']
cluster_options['worker_cores'] = 1
cluster_options['worker_cores_limit'] = 2
cluster_options['worker_memory'] = "2 G"
# Create a new cluster with the specified options
cluster = gateway.new_cluster(cluster_options)

print(f"Cluster dashboard: {cluster.dashboard_link}")
# Scale the cluster as needed
cluster.scale(5)

# Use the cluster
from dask.distributed import Client
client = Client(cluster)

sleep(30)
client.close()

cluster.shutdown()