# Burned Area Intensity CWL on Kubernetes with Calrissian

This example runs an application package to derive the burned area intensity using a pre and post event pair of Sentinel-2 STAC items.

The command line tool claims a Dask cluster to support the calculations.

## Pre-requirements

- You are running `skaffold dev` under the folder `dask-gateway` (root folder) in a dedicated shell. Whithin the minikube cluster, the Dask Gateway is accessible at "http://traefik-dask-gateway.dask-gateway.svc.cluster.local:80".
- You are running `skaffold dev` under this folder (`dask-gateway/example/option-b`) in a dedicated shell.

The skaffold configuration includes:

- a container image with the `bai.py` code and its dependencies (the files are in the folder `dask-gateway/example/option-b/bai`)
- a helm release that installs the local Helm Chart `bai-chart` (the files are in the folder `dask-gateway/example/option-b/bai-chart`). This Helm Chart creates:
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

In `/data/work/dev-platforms/dask-gateway/example/option-b`, run `skaffold dev`

In `/data/work/dev-platforms/dask-gateway/example/option-b`, run `kubectl apply -n dask-gateway -f job.yaml`. Monitor the job execution and in particular the calrissian pod log.

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

## Explanation

Platform deploys a Dask Gateway in Eric’s workspace.

Eric writes an application package with a CommandLineTool that requires a Dask Gateway to procure a Dask cluster

At runtime, the CWL runner mounts the Dask Gateway configuration file: 

```yaml
gateway:
  address: "http://traefik-dask-gateway.ws-eric.svc.cluster.local:80"

  cluster:
    options: 
      image: "cr.terradue.com/eoepca-plus/bai:bccfd21"
      worker_cores: 0.5
      worker_cores_limit: 1
      worker_memory: "4 G"
```

The image value is the same as the `DockerRequirement` in CWL document written by Eric.

The Dask Gateway URL is set to Eric’s Dask Gateway deployed in his workspace.

The CWL runner claims the Dask cluster (code simplified):

```python
gateway = Gateway()
cluster = gateway.new_cluster(shutdown_on_close=False)

max_cores = 5 # would come from DaskGateway.Requirement.ResourceRequirement.max_cores
max_ram = 16  # would come from DaskGateway.Requirement.ResourceRequirement.max_ram

cluster.scale(workers)
```

The CWL command line tool is executed with:

```
python -m app --pre_fire_url https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_10TFK_20210713_0_L2A --post_fire_url https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2A_10TFK_20210718_0_L2A
```
and logs: 

```
2024-10-07 13:31:53.937 | INFO     | __main__:<module>:114 - Dask Dashboard: http://traefik-dask-gateway.dask-gateway.svc.cluster.local:80/clusters/dask-gateway.aaf1dadbd74b4f32a584ef08fee4701a/status
2024-10-07 13:31:53.937 | INFO     | __main__:<module>:115 - Running the burned area intensity
2024-10-07 13:31:53.938 | INFO     | __main__:main:14 - pre event https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_10TFK_20210713_0_L2A
2024-10-07 13:31:53.938 | INFO     | __main__:main:15 - post event https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2A_10TFK_20210718_0_L2A
2024-10-07 13:31:56.627 | INFO     | __main__:main:71 - Burnt area intensity shape: (10980, 10980)
2024-10-07 13:31:56.628 | INFO     | __main__:main:72 - Burnt area intensity dims: ('y', 'x')
2024-10-07 13:31:56.644 | INFO     | __main__:main:84 - Writing the result to a COG file
```

Finally the CWL runner dismisses the Dask cluster.

```python
gateway = Gateway()
cluster = gateway.connect(os.environ["DASK_GATEWAY_CLUSTER"])
cluster.shutdown()
```





