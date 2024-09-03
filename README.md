# Dask Gateway

Bootstraps a dask gateway deployment on minikube using skaffold.

The Dask worker pods run the image that is defined by the `Dockerfile.worker` file.

The client pod runs the image that is defined by the `Dockerfile.client` file.

In Dask, the client, the scheduler and the workers must run the same Python libraries, so:

- the local development environment is created using the same dependencies defined in `requirements.txt` with `pip install -r requirements.txt`
- the client pod that can be used via shell in kubernetes, also uses `pip install -r requirements.txt`, a line in the `Dockerfile.client` file
- the workers also use `pip install -r requirements.txt`, a line in the `Dockerfile.worker` file

An update in `requirements.txt` and/or in the `Dockerfile.*` triggers an update of the Dask Gateway deployment.

## Requirements

* Minikube [installation](https://minikube.sigs.k8s.io/docs/start/?arch=%2Flinux%2Fx86-64%2Fstable%2Fbinary+download)
* skaffold [installation](https://skaffold.dev/docs/install/#standalone-binary)

## Setup

Start your minikube cluster:

```
minikube start
```

Install Dask Gateway development platform with:

```
skaffold dev
```
This builds and pushes two container images to minikube node image cache: 

- the worker image `worker` built with the docker file `Dockerfile.worker`
- the client image `daskclient` built with the docker file `Dockerfile.client`

And installs two helm releases:

- `dask-gateway` using the chart https://helm.dask.org/dask-gateway-2024.1.0.tgz. The values set the worker image built with the docker file `Dockerfile.worker`. The Dask Gateway configuration is extended to allow clients to set `image`, `worker_cores`, `worker_cores_limit` and `worker_memory` (see the file `dask-gateway/values.yalm`)
- `dask-session` a local chart creating a deployment with a pod running the image built with the docker file `Dockerfile.client`


Wait for the deployment to stabilize, the logs will show the tags of the built images, e.g.:

```
Tags used in deployment:
 - worker -> worker:3853d0ad064e3f6b76696a81c99148113b44ac297759843d4c302017d4abaf45
 - daskclient -> daskclient:fc88475cf797d64f0069d3bb4119a86d092b8d9761c77dfa882aa845f2e53be5
```



```
Checking cache...
 - worker: Found. Tagging
 - daskclient: Found. Tagging
Tags used in deployment:
 - worker -> worker:3853d0ad064e3f6b76696a81c99148113b44ac297759843d4c302017d4abaf45
 - daskclient -> daskclient:fc88475cf797d64f0069d3bb4119a86d092b8d9761c77dfa882aa845f2e53be5
Starting deploy...
Helm release dask-gateway not installed. Installing...
NAME: dask-gateway
LAST DEPLOYED: Fri Jul  5 16:43:16 2024
NAMESPACE: dask-gateway
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
You've installed Dask-Gateway version 2024.1.0, from chart
version 2024.1.0!

Your release is named "dask-gateway" and installed into the
namespace "dask-gateway".

You can find the public address(es) at:

  $ kubectl --namespace=dask-gateway get service traefik-dask-gateway
Helm release dask-session not installed. Installing...
NAME: dask-session
LAST DEPLOYED: Fri Jul  5 16:43:17 2024
NAMESPACE: dask-gateway
STATUS: deployed
REVISION: 1
TEST SUITE: None
WARN[0012] image [worker:3853d0ad064e3f6b76696a81c99148113b44ac297759843d4c302017d4abaf45] is not used.  subtask=-1 task=DevLoop
WARN[0012] See helm documentation on how to replace image names with their actual tags: https://skaffold.dev/docs/pipeline-stages/deployers/helm/#image-configuration  subtask=-1 task=DevLoop
Waiting for deployments to stabilize...
 - dask-gateway:deployment/controller-dask-gateway is ready. [3/4 deployment(s) still pending]
 - dask-gateway:deployment/dask-session is ready. [2/4 deployment(s) still pending]
 - dask-gateway:deployment/api-dask-gateway: waiting for rollout to finish: 0 of 1 updated replicas are available...
 - dask-gateway:deployment/traefik-dask-gateway: waiting for rollout to finish: 0 of 1 updated replicas are available...
 - dask-gateway:deployment/traefik-dask-gateway is ready. [1/4 deployment(s) still pending]
 - dask-gateway:deployment/api-dask-gateway is ready.
Deployments stabilized in 10.081 seconds
Starting post-deploy hooks...
Deployment replicas: 1
Deployment with label app.kubernetes.io/name=dask-gateway is running
Completed post-deploy hooks
Port forwarding service/traefik-dask-gateway in namespace dask-gateway, remote port 80 -> http://127.0.0.1:8001
Listing files to watch...
 - worker
 - daskclient
Press Ctrl+C to exit
Watching for changes...
```

Open the browser on https://127.0.0.1:8001, this will print `404: Not Found`. This is ok, it is the Dask Gateway port forward that you can use from your local development environment.


## Getting started

### Local client running on your machine

Create a Python environment with:

```
python3 -m venv env_test_dask
source env_test_dask/bin/activate
pip install -r requirements.txt
```

Use the Python code below to get started:

```
from time import sleep
from dask_gateway import Gateway

gateway = Gateway("http://localhost:8001")

from dask_gateway import GatewayCluster
cluster = gateway.new_cluster()

print("Scaling cluster to 4 workers")
cluster.scale(4)
client = cluster.get_client()

print(f"Cluster dashboard: {cluster.dashboard_link}")

sleep(60)

cluster.shutdown()
```

### Access the dask client pod 

Open a shell on the dask-session deployment pod. There are two environment variables set:

- `DASK_GATEWAY_URL`: the Dask Gateway endpoint
- `DASK_WORKER_IMAGE`: the container image for the dask scheduler and workers


## Dask Cluster configuration 

This section is informative.

### Set the worker container image at runtime

If the `dask-gateway` Helm chart values includes:

```yaml
gateway:
  extraConfig:
    dask_gateway_config.py: |
      c = get_config()
      from dask_gateway_server.options import Options, String
      c.Backend.cluster_options = Options(
          String("image", default="daskgateway/dask-worker:latest", label="Worker Image")
      )
```

Then the Python code may define the Dask scheduler and workers' image: 


```python
from dask_gateway import Gateway
from time import sleep
# Connect to the Dask Gateway
gateway = Gateway("http://localhost:8001")

# Define cluster options with a custom worker container image
cluster_options = gateway.cluster_options()

print(cluster_options)
cluster_options['image'] = 'docker.io/library/worker:5ee153c-dirty'

# Create a new cluster with the specified options
cluster = gateway.new_cluster(cluster_options)

# Scale the cluster as needed
cluster.scale(5)

# Use the cluster
from dask.distributed import Client
client = Client(cluster)

sleep(30)

cluster.shutdown()
```

### Set the worker cores and memory

If the Helm chart values includes:

```yaml
gateway:
  extraConfig:
    dask_gateway_config.py: |
      c = get_config()
      from dask_gateway_server.options import Options, String, Integer
      c.Backend.cluster_options = Options(
            Integer("worker_cores_limit", default=1, label="Worker Cores Limit"),
            Integer("worker_cores", default=1, label="Worker Cores"),
            String("worker_memory", default="1 G", label="Worker Memory"),
      )
```

Then you can use:

```python
from dask_gateway import Gateway
from time import sleep
# Connect to the Dask Gateway
gateway = Gateway("http://localhost:8001")

# Define cluster options 
cluster_options = gateway.cluster_options()

cluster_options['worker_cores'] = 1
cluster_options['worker_cores_limit'] = 2
cluster_options['worker_memory'] = "2 G"

# Create a new cluster with the specified options
cluster = gateway.new_cluster(cluster_options)

# Scale the cluster as needed
cluster.scale(5)

# Use the cluster
from dask.distributed import Client
client = Client(cluster)

sleep(30)
client.close()

cluster.shutdown()
```

The `dask-gateway` helm chart values defines:

```python
c = get_config()
      from dask_gateway_server.options import Options, String, Integer, Float
      c.Backend.cluster_options = Options(
        Float("worker_cores_limit", default=1, label="Worker Cores Limit"),
        Float("worker_cores", default=1, label="Worker Cores"),
        String("worker_memory", default="1 G", label="Worker Memory"),
        String("image", default="daskgateway/dask-worker:latest", label="Worker Image")
      )
```

so `worker_cores_limit`, `worker_cores`, `worker_memory` and `image` can be defined.