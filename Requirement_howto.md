# How to painlessly add a new requirement

## Define your own extension

```
- name: DaskGatewayRequirement
  type: record
  extends: cwl:ProcessRequirement
  inVocab: false
  doc: "Indicates that a process requires a [Dask Gateway](https://gateway.dask.org/) runtime."
  fields:
    class:
      type: string
      doc: 'cwltool:DaskGatewayRequirement'
      jsonldPredicate:
        "_id": "@type"
        "_type": "@vocab"
    workerCores:
      type:
        - 'int'
        - 'cwl:Expression'
      doc: |
        Number of cpu-cores available for a Dask worker.
    workerCoresLimit:
      type:
        - 'string'
        - 'cwl:Expression'
      doc: |
        Maximum number of cpu-cores available for a Dask worker.
    workerMemory:
      type:
        - 'int'
        - 'cwl:Expression'
      doc: |
        Maximum number of bytes available for a Dask worker.
```

Pay attention on `extends: cwl:ProcessRequirement` otherwise it won't be recognized.

## Add the requirement in the current CWL version

```
git clone https://github.com/common-workflow-language/cwl-v1.2/
cd cwl-v1.2/
git checkout codegen
vim extensions.yml
[add your extension here]
```

## Recreate the cwl-utils parser

```
cd ../
git clone git@github.com:common-workflow-language/cwl-utils.git
cd cwl-utils/
schema-salad-tool --codegen python ../cwl-v1.2/extensions.yml --codegen-parser-info "org.w3id.cwl.v1_2" > cwl_utils/parser/cwl_v1_2.py
pip install -e .
```

## Enable the extension in the cwltool

```
cd ../
git clone git@github.com:common-workflow-language/cwltool.git
cd cwltool
```

Add your extension as well in `cwltool`:

```
vim cwltool/extensions-v1.2.yml
[add your extension here, also]
```

Enable the extension via the FQN:

```
vim cwltool/process.py
[add "http://commonwl.org/cwltool#DaskGatewayRequirement" in the 'supportedProcessRequirements' list]
```

Not required, but just for the sake of better `cwl-utils` version binding, put `cwl-utils>=0.36` in following files:

```
cwltool/main.py
mypy-requirements.txt
pyproject.toml
requirements.txt
setup.py
```

Then reinstall the tool

```
pip install -e .
```

## Verify the extension is working

```
cd ../
cd dev-platform-dask-gateway/example/pod-procure
cwltool --enable-ext --validate --debug example.cwl
```
