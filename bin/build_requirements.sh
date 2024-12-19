#!/bin/bash

BASEDIR=`dirname $0`
BASEDIR=`(cd ${BASEDIR}/..; pwd)`
TARGET=${BASEDIR}/target

rm -rf ${TARGET}
mkdir -p ${TARGET}
cd ${TARGET}

# add the new requirement(s) to the extensions

git clone https://github.com/common-workflow-language/cwl-v1.2/
cd cwl-v1.2/
git checkout codegen
cat ${BASEDIR}/bin/DaskGatewayRequirement.yaml >> extensions.yml

# rebuild the cwl-utils

cd ../
git clone git@github.com:common-workflow-language/cwl-utils.git
cd cwl-utils/
sed -i 's,https://github.com/common-workflow-language/cwl-v1.2/raw/codegen/extensions.yml,../cwl-v1.2/extensions.yml,g' Makefile
make cwl_utils/parser/cwl_v1_2.py all

## rebuild the cwl-tool

cd ../
git clone git@github.com:common-workflow-language/cwltool.git
cd cwltool
cat ${BASEDIR}/bin/DaskGatewayRequirement.yaml >> cwltool/extensions-v1.2.yml
sed -i 's@"http://commonwl.org/cwltool#TimeLimit"@"http://commonwl.org/cwltool#DaskGatewayRequirement", "http://commonwl.org/cwltool#TimeLimit"@g' cwltool/process.py
sudo rm -rf /usr/lib/python3/dist-packages/cwltool/
make all

cd ../

cwltool --enable-ext --validate --debug ${BASEDIR}/example/pod-procure/example.cwl

