#!/usr/bin/env bash
set -e

# Defaults, Can be overrided by args
STACK_NAME="SpandelEngine"
DEPLOY_BUCKET_PARAM="/Deploy/Bucket"

# Config
# What container is used to install dependencies, must have pip installed
CONTAINER="python:3.7"
SCRIPT_DIR="$(cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# Process Args
while [[ $# -gt 0 ]] ; do
    key="$1"
    case ${key} in
        --stack-name)
        STACK_NAME="$2"
        shift # past argument
        shift # past value
        ;;
        # SSM Param with bucket name
        --bucket-param)
        DEPLOY_BUCKET_PARAM="$2"
        shift # past argument
        shift # past value
        ;;
        # S3 Bucket name. Can be used to specify different bucket than what is in SSM Param
        --bucket)
        BUCKET="$2"
        shift # past argument
        shift # past value
        ;;
         # specify parameter-overrides to be used with the sam deploy command. "ParamKey1=ParamValue ParamKey2=ParamValue"
        --parameter-overrides)
        PARAMS="$2"
        shift # past argument
        shift # past value
        ;;
         # will skip pip install of dependencies and create a layer based off of previous installed dependencies
        --use-existing-dependencies)
        USE_EXISTING_DEPENDS=true
        shift # past argument
        ;;
    esac
done

mkdir -p ${SCRIPT_DIR}/scratch

if [[ -z ${BUCKET} ]] ; then
    BUCKET=$(aws ssm get-parameter --name ${DEPLOY_BUCKET_PARAM} --query "Parameter.Value" --output text)
    if [[ $? -ne 0 ]] ; then
        echo "Unable to get bucket name from SSM Param ${DEPLOY_BUCKET_PARAM}"
        exit 1
    fi
fi

if [[ -z ${USE_EXISTING_DEPENDS} ]] ; then
    echo "Installing dependencies using container ${CONTAINER}. The WARNINGs generated by pip can be ignored."
    rm -rf ${SCRIPT_DIR}/scratch/layers/python
    mkdir -p ${SCRIPT_DIR}/scratch/layers/python
    docker run -v "${SCRIPT_DIR}:/project" -u $(id -u ${USER}) ${CONTAINER} pip install -q -r /project/requirements.txt -t /project/scratch/layers/python
else
    if [[ ! -d scratch/layers/python ]] ; then
        echo "Dependencies dir for layers appears to be missing. Run once without --use-existing-dependencies"
        exit 1
    fi
fi

aws cloudformation package --s3-bucket ${BUCKET} --template-file ${SCRIPT_DIR}/template.yaml --output-template-file ${SCRIPT_DIR}/scratch/${STACK_NAME}.yaml
# Deploy packaged template
DEPLOY_CMD="aws cloudformation deploy --template-file ${SCRIPT_DIR}/scratch/${STACK_NAME}.yaml --stack-name ${STACK_NAME} --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
"
if [[ -n ${PARAMS} ]] ; then
    DEPLOY_CMD="${DEPLOY_CMD} --parameter-overrides ${PARAMS}"
fi
eval ${DEPLOY_CMD}

SHARED_RESOURCE_BUCKET=$(
    aws cloudformation describe-stacks --stack-name ${STACK_NAME} \
    --query "Stacks[0].Outputs[?OutputKey=='SharedResourcesBucketName'].OutputValue" --output text
)

