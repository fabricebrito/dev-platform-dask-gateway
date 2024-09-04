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
        ResourceRequirement:
          coresMax: 1
          ramMax: 512
        InitialWorkDirRequirement:
          listing:
            - entryname: gateway.yaml
              entry: |
                gateway:
                  address: "{{ .Values.daskGatewayUrl }}"
                
                  cluster:
                    options: 
                      image: "{{ .Values.daskWorkerImage }}"
                      worker_cores: 0.5
                      worker_cores_limit: 1
                      worker_memory: "4 G"
                    

            - entryname: procure.py
              entry: |-
                # this code is responsible for creating a Dask cluster
                # it's executed by the CWL runner in the context of the Dask Gateway extension
                # this is for the prototyping purposes only
                import os
                from dask_gateway import Gateway

                gateway = Gateway()

                cluster = gateway.new_cluster(shutdown_on_close=False)
                cluster.scale(4)
                # save the cluster name to a file
                with open("dask_cluster_name.txt", "w") as f:
                  f.write(cluster.name)
                #
            - entryname: shutdown.py
              entry: |-
                # this code is responsible for dismissing a Dask cluster
                # it's executed by the CWL runner in the context of the Dask Gateway extension
                # this is for the prototyping purposes only
                import os
                from dask_gateway import Gateway

                gateway = Gateway()

                cluster = gateway.connect(os.environ["DASK_GATEWAY_CLUSTER"])

                cluster.shutdown()

            - entryname: run.sh
              entry: |-
                #!/bin/bash

                # this is done by the CWL runner in the context of the Dask Gateway extension
                # as a preparation for the execution of the main script
                # this is for the prototyping purposes only

                set -x
                rm -f $HOME/.config/dask/gateway.yaml
                mkdir -p /etc/dask
                #mkdir -p $HOME/.config/dask
                cp -v gateway.yaml /etc/dask/gateway.yaml
                #cp -v gateway.yaml $HOME/.config/dask/gateway.yaml
                #chmod 600 $HOME/.config/dask/gateway.yaml
                chmod 600 /etc/dask/gateway.yaml
                cat /etc/dask/gateway.yaml

                #cat $HOME/.config/dask/gateway.yaml

                python procure.py
                export DASK_GATEWAY_CLUSTER=` cat dask_cluster_name.txt `

                # this is executed as usual by the CWL runner
                python -m app --pre_fire_url $( inputs.pre_event ) --post_fire_url $( inputs.post_event )
                
                # this is done by the CWL runner in the context of the Dask Gateway extension
                # as a post step after the execution of the main script
                # this is for the prototyping purposes only
                python shutdown.py

                #
    hints:
      DockerRequirement:
        dockerPull: "{{ .Values.daskWorkerImage }}"
    baseCommand: ['/bin/sh', 'run.sh']
    arguments: []
    inputs:
      pre_event:
        type: string

      post_event:
        type: string
      
    outputs:
      burned_area_intensity:
        outputBinding:
            glob: bai.tif
        type: File


