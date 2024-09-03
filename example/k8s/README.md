# Burned Area Intensity CWL on Kubernetes with Calrissian

This example runs an application package to derive the burned area intensity using a pre and post event pair of Sentinel-2 STAC items.

The command line tool claims a Dask cluster to support the calculations.

## Pre-requirements

- You are running `skaffold dev` under the folder `dask-gateway` (root folder) in a dedicated shell. Whithin the minikube cluster, the Dask Gateway is accessible at "http://traefik-dask-gateway.dask-gateway.svc.cluster.local:80".
- You are running `skaffold dev` under this folder (`dask-gateway/example/k8s`) in a dedicated shell.

The skaffold configuration includes:

- a container image with the `bai.py` code and its dependencies (the files are in the folder `dask-gateway/example/k8s/bai`)
- a helm release that installs the local Helm Chart `bai-chart` (the files are in the folder `dask-gateway/example/k8s/bai-chart`). This Helm Chart creates:
  - a `PersistentVolumeClaim` for Calrissian
  - roles and role bindings for Calrissian
  - a config map with the BAI Application Package that will be mounted on the calrissian pod
  - a service account to run Calrissian  

The config map with the BAI Application Package uses the Application Package in JSON format and it was converted from YAML to JSON with:

```
cat bai.cwl | yq e . -o=json - > bai-chart/files/app-package.json
```

## Notes 

- dask container uid (uid 0) must match job uid (running as user 0). The container images will be updated to use `1000:1000`.

## Running the example

In `/data/work/dev-platforms/dask-gateway`, run `skaffold dev`

In `/data/work/dev-platforms/dask-gateway/example/k8s`, run `skaffold dev`

In `/data/work/dev-platforms/dask-gateway/example/k8s`, run `kubectl apply -n dask-gateway -f job.yaml`. Monitor the job execution and in particular the calrissian pod log.

The pod `node-bai-xxx` will show: 

```
2024-09-03 06:16:15.215 | INFO     | __main__:<module>:110 - Procuring a new Dask cluster
2024-09-03 06:16:24.206 | INFO     | __main__:<module>:125 - Adapting cluster: minimum=4, maximum=5
2024-09-03 06:16:24.407 | INFO     | __main__:<module>:128 - Dask Dashboard: http://traefik-dask-gateway.dask-gateway.svc.cluster.local:80/clusters/dask-gateway.9544e95eeec64b1aaa03ddd8a79036bb/status
2024-09-03 06:16:24.407 | INFO     | __main__:<module>:129 - Running the burned area intensity
2024-09-03 06:16:24.407 | INFO     | __main__:main:14 - pre event https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_10TFK_20210713_0_L2A
2024-09-03 06:16:24.407 | INFO     | __main__:main:15 - post event https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2A_10TFK_20210718_0_L2A
2024-09-03 06:16:26.112 | INFO     | __main__:main:71 - Burnt area intensity shape: (10980, 10980)
2024-09-03 06:16:26.113 | INFO     | __main__:main:72 - Burnt area intensity dims: ('y', 'x')
2024-09-03 06:16:26.152 | INFO     | __main__:main:84 - Writing the result to a COG file
```

Access the Dask dashboard using the link: http://127.0.0.1:8001/clusters/dask-gateway.9544e95eeec64b1aaa03ddd8a79036bb/status

## The Thing to solve for CWL portability

The developer sets the expected environment variables in his/her code for creating a dask cluster using the Dask Gateway.

The environment variables are mapped to Dask Gateway settings:

- image (worker and scheduler image)
- worker_cores
- worker_cores_limit
- worker_memory

An environment variable sets the Dask Gateway URL. The value is provided at runtime.

To showcase the issue, the developer includes in the CWL:

```json
"requirements": {
        "InlineJavascriptRequirement": {},
        "EnvVarRequirement": {
          "envDef": {
            "PYTHONPATH": "/app",
            "DASK_GATEWAY_URL": "http://traefik-dask-gateway.dask-gateway.svc.cluster.local:80",
            "DASK_WORKER_IMAGE": "bai:eb7fe8f144176e3ca5f6a391cc007a776138647c8102fa2388e4687f484d5f02",
            "DASK_WORKER_CORES": "0.5",
            "DASK_WORKER_CORES_LIMIT": "1",
            "DASK_WORKER_MEMORY": "4 G"
          }
        }
}
```

And in his/her Python code:

```python
gateway = Gateway(os.getenv("DASK_GATEWAY_URL"))

logger.info("Procuring a new Dask cluster")

# Define cluster options with a custom worker container image
cluster_options = gateway.cluster_options()
cluster_options[
    "image"
] = os.getenv("DASK_WORKER_IMAGE")
cluster_options["worker_cores"] = float(os.getenv("DASK_WORKER_CORES"))
cluster_options["worker_cores_limit"] = float(os.getenv("DASK_WORKER_CORES_LIMIT"))
cluster_options["worker_memory"] = os.getenv("DASK_WORKER_MEMORY")

# Create a new cluster with the specified options
cluster = gateway.new_cluster(cluster_options)
```

The environment variables are arbitrary and their name are defined by the developer.

A CWL extension needs to map the Dask Gateway configuration items and gateway URL to the developer defined environment variables, for example:

```yaml
DaskGatewayRequirement:
    EnvVarRequirement:
        worker_cores: DASK_WORKER_CORES # defined by the developer
        worker_cores_limit: DASK_WORKER_CORES_LIMIT # defined by the developer
        worker_memory: DASK_WORKER_MEMORY # defined by the developer
        gateway_url: DASK_GATEWAY_URL # defined by the developer, set at runtime by the CWL runner
        image: DASK_WORKER_IMAGE # defined by the developer
    RuntimeRequirement: 
        min_cores: 4 # set by the developer
        max_cores: 10 # set by the developer
        worker_cores: 0.5 # set by the developer
        worker_cores_limit: 1 # set by the developer
        worker_memory: "4 G" # set by the developer
        image: "bai:eb7fe8f144176e3ca5f6a391cc007a776138647c8102fa2388e4687f484d5f02" # set by the developer or the CI
```

or (WIP)

```yaml
DaskGatewayRequirement:
  cores_min: 
    value: 4  # set by the developer
  cores_max: 
    value: 10  # set by the developer
  worker_cores: 
    name: "DASK_WORKER_CORES"  # defined by the developer
    value: 0.5  # set by the developer
  worker_cores_limit: 
    name: "DASK_WORKER_CORES_LIMIT" # defined by the developer
    value: 1  # set by the developer
  worker_memory: 
    name: "DASK_WORKER_MEMORY" # defined by the developer
    value: "4 G"  # set by the developer
  gateway_url: 
    name: "DASK_GATEWAY_URL" # defined by the developer, value set at runtime by the CWL runner
  image:
    name: DASK_WORKER_IMAGE # defined by the developer
    value: "bai:eb7fe8f144176e3ca5f6a391cc007a776138647c8102fa2388e4687f484d5f02" # set by the developer or the CI
```

With this CWL extension for the Dask Gateway, CWL developers can map the environment variable their code expects.
The `gateway_url` is the Dask Gateway endpoint and a CWL runner supporting this extension provides the value to the environment variable at runtime.

Thus, at runtime, the CWL runner creates the environment variables:

```bash
DASK_GATEWAY_URL="http://traefik-dask-gateway.dask-gateway.svc.cluster.local:80" # set at runtime
DASK_WORKER_IMAGE="bai:eb7fe8f144176e3ca5f6a391cc007a776138647c8102fa2388e4687f484d5f02" # set in the CWL by the developer or CI
DASK_WORKER_CORES="0.5" # set by the developer
DASK_WORKER_CORES_LIMIT="1" # set by the developer
DASK_WORKER_MEMORY="4 G" # set by the developer
```

Dask Gateway implementation includes other configuration items that are computing environment dependent for e.g. HPC or Kubernetes.

These items must be part of the CWL extension for Dask Gateway and the objective is to support the local, HPC and Kubernetes CWL execution with the priority on local and kubernetes.

