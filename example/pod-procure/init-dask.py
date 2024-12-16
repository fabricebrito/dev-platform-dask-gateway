# this code is responsible for creating a Dask cluster
# it's executed by the CWL runner in the context of the Dask Gateway extension
# this is for the prototyping purposes only
import os
import argparse
from loguru import logger
from dask_gateway import Gateway

# read the arguments containing the target file path for the Dask cluster name
parser = argparse.ArgumentParser()
parser.add_argument("--target", type=str, required=True)
args = parser.parse_args()

target = args.target

logger.info(f"Creating Dask cluster and saving the name to {target}")

gateway = Gateway()

cluster = gateway.new_cluster(shutdown_on_close=False)

# resource requirements
worker_cores = 0.5
worker_cores_limit = 1 # would come from DaskGateway.Requirement.ResourceRequirement.worker_cores_limit (or worker_cores)
worker_memory = 2 # would come from DaskGateway.Requirement.ResourceRequirement.worker_memory
logger.info(f"Resource requirements: {worker_cores} cores, {worker_memory} GB RAM")

# scale cluster
max_cores = 5 # would come from DaskGateway.Requirement.ResourceRequirement.max_cores
max_ram = 16  # would come from DaskGateway.Requirement.ResourceRequirement.max_ram
logger.info(f"Resource limits: {max_cores} cores, {max_ram} GB RAM")

workers = min(max_cores // worker_cores_limit, max_ram // worker_memory)
logger.info(f"Scaling cluster to {workers} workers")
cluster.scale(workers)


# save the cluster name to a file
with open(target, "w") as f:
    f.write(cluster.name)
logger.info(f"Cluster name {cluster.name} saved to {target}")