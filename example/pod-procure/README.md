
## Dask cluster initialization

Cluster options:

**User defined via CWL CommandLineTool `DaskGatewayRequirement`:**

- worker-cores
- worker-memory
- worker-cores-limit
- image

**Runner defined:** 

- gateway URL

This is a `gateway-config.yaml` file mounted on the main container 

**k8s limits for the number of workers:**

- max-cores
- max-ram

## Communication between containers in Pod

* init -> main: 

cluster name: implemented with the cluster name in a text file: `/shared/dask_cluster_name.txt`

environment variable `DASK_CLUSTER` with the content of `/shared/dask_cluster_name.txt`

* main -> sidecar 

completion signal: implemented with an empty file in `/shared/completed`

cluster name: implemented with the cluster name in a text file: `/shared/dask_cluster_name.txt`


## DaskGatewayRequirement CWL extension


```yaml
DaskGatewayRequirement:
    ResourceRequirement:
        workerCores: 0.5
        workerCoresLimit: 1
        workerMemory: 2
        coresMax: 5
        ramMax: 16
```
