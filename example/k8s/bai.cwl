cwlVersion: v1.0
$namespaces:
  s: https://schema.org/
s:softwareVersion: 1.0.0
schemas:
  - http://schema.org/version/9.0/schemaorg-current-http.rdf
$graph:
  - class: Workflow
    id: main
    label: Burned area intensity
    doc: Burned area intensity
    requirements: []
    inputs:
      pre_event:
        label: pre-event STAC item
        doc: pre-event STAC item
        type: string
      post_event:
        label: post-event STAC item
        doc: post-event STAC item
        type: string
    outputs:
      - id: bai
        outputSource:
          - node_bai/burned_area_intensity
        type: File
    steps:
      node_bai:
        run: "#bai"
        in:
          pre_event: pre_event
          post_event: post_event
        out:
          - burned_area_intensity
  - class: CommandLineTool
    id: bai
    requirements:
        InlineJavascriptRequirement: {}
        EnvVarRequirement:
          envDef:
            PYTHONPATH: /app
            DASK_GATEWAY_URL: "{{ .Values.daskGatewayUrl }}"
            DASK_WORKER_IMAGE: "{{ .Values.daskWorkerImage }}"
            DASK_WORKER_CORES: "0.5"
            DASK_WORKER_CORES_LIMIT: "1"
            DASK_WORKER_MEMORY: "4 G"
        ResourceRequirement:
          coresMax: 1
          ramMax: 512
    hints:
      DockerRequirement:
        dockerPull: "{{ .Values.dockerPull }}"
    baseCommand: ["python", "-m", "app"]
    arguments: []
    inputs:
      pre_event:
        type: string
        inputBinding:
            prefix: --pre_fire_url
      post_event:
        type: string
        inputBinding:
            prefix: --post_fire_url
      
    outputs:
      burned_area_intensity:
        outputBinding:
            glob: bai.tif
        type: File


