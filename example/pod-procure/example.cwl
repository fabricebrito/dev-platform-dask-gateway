#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool
label: Example
doc: Example

requirements:
  
  SchemaDefRequirement:
    types:
    - $import: https://raw.githubusercontent.com/fabricebrito/dev-platform-dask-gateway/refs/heads/main/example/pod-procure/schema.yaml

  DaskGatewayRequirement:
    type: https://raw.githubusercontent.com/fabricebrito/dev-platform-dask-gateway/refs/heads/main/example/pod-procure/schema.yaml#SchemaDefRequirement

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
