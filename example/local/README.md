
# WORK IN PROGRESS...

# Burned area intensity using Sentinel-2

This example how the local development of Dask based applications may be conducted.
 
The code reads a pre and post event pair of Sentinel-2 STAC items and generates a geotiff with the burned area intensity.

The example can either use a Dask Gateway deployed on minikube and exposed as a port forward and or use a Dask Gateway installed in a Python environment.

## Pre-requirements

### Dask Gateway on minikube

- You are running `skaffold dev` under the folder `dask-gateway` (root folder) and you have a port forward for the Dask Gateway service on "http://localhost:8001"
- You have created a Python environment with (under the folder `dask-gateway`, root folder):

```bash
python3 -m venv env_test_dask
source env_test_dask/bin/activate
pip install -r requirements.txt
```

### Dask Gateway installed in a Python environment

Use pip to install Dask Gateway:

```
pip install dask-gateway dask-gateway-server[local]
```

To start the Gateway server, run:

```
dask-gateway-server
```

By default the gateway URL is http://127.0.0.1:8000.

## Run the example

In a shell, run 

```
python bai.py 
```

This prints:

```
Traceback (most recent call last):
  File "/data/work/dev-platforms/dask-gateway/example/local/bai.py", line 1, in <module>
    import stackstac
ModuleNotFoundError: No module named 'stackstac'
```

The client environment does not include `stackstac` required to run the `bai.py` code. The client, Dask scheduler and Dask workers need to run the same libraries with the same versions. 

To fix this, you need two actions:

- In the root folder (`dask-gateway`), edit the `requirements.txt` to add `stackstac` so the Dask worker container image is rebuilt and pushed to minikube by `skaffold`
- In the folder `dask-gateway/local` containing the `bai.py` file, run `pip install -r ../../requirements.txt` to update the local virtual environment (Dask client)

In the first step above `skaffold` prints at some stage:

```
Build [worker] succeeded
Tags used in deployment:
 - worker -> worker:3853d0ad064e3f6b76696a81c99148113b44ac297759843d4c302017d4abaf45
 - daskclient -> daskclient:fc88475cf797d64f0069d3bb4119a86d092b8d9761c77dfa882aa845f2e53be5
Starting deploy...
```

These are the new container image tags. We'll use the `worker` container image tag and update the `bai.py` file in section:

```python
cluster_options = gateway.cluster_options()

cluster_options['image'] = 'worker:3853d0ad064e3f6b76696a81c99148113b44ac297759843d4c302017d4abaf45'
cluster_options['worker_cores'] = 1
cluster_options['worker_cores_limit'] = 1
cluster_options['worker_memory'] = "1 G"
# Create a new cluster with the specified options
cluster = gateway.new_cluster(cluster_options)
```

Now verify the outcome of the second step with:

```
python -c "import stackstac"
```

The `ModuleNotFoundError` exception is now gone.

Now, run the `bai.py` script again.

```
python bai.py 
```

The output looks like:

```
(env_test_dask) (base) fbrito@fbrito-ThinkPad-P15-Gen-1:/data/work/dev-platforms/dask-gateway/example/local$ python bai.py 
2024-07-05 11:02:55.296 | INFO     | __main__:<module>:79 - Procuring a new Dask cluster
2024-07-05 11:02:59.791 | INFO     | __main__:<module>:95 - Adapting cluster: minimum=4, maximum=10
/data/work/dev-platforms/dask-gateway/env_test_dask/lib/python3.10/site-packages/distributed/client.py:1391: VersionMismatchWarning: Mismatched versions found

+---------+-----------------+-----------------+---------+
| Package | Client          | Scheduler       | Workers |
+---------+-----------------+-----------------+---------+
| python  | 3.10.12.final.0 | 3.10.14.final.0 | None    |
+---------+-----------------+-----------------+---------+
  warnings.warn(version_module.VersionMismatchWarning(msg[0]["warning"]))
Dask Dashboard: http://localhost:8001/clusters/dask-gateway.cf328df2de524496a938bf990d422ee1/status
```

Open the dashboard and wait for the conclusion of the processing. It takes a few minutes.