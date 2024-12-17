#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool
label: Example
doc: Example

$namespaces:
  dask: "https://www.terradue.com/dask/schema#"

$schemas:
    - https://raw.githubusercontent.com/fabricebrito/dev-platform-dask-gateway/refs/heads/main/example/pod-procure/schema.yaml

requirements:
  dask:DaskGatewayRequirement:
    class: DaskGatewayRequirement
    workerCores: 2
    workerCoresLimit: "4"
    workerMemory: 1073741824   # 1 GiB in bytes
    coresMax: "8"
    ramMax: "16Gi"

inputs:
  post_event:
    type: string
    inputBinding:
      prefix: --post-event
      position: 2
  pre_event:
    type: string
    inputBinding:
      prefix: --pre-event
      position: 1

outputs:
  bai:
    type: File
    outputBinding:
      glob: bai.tif
id: example
