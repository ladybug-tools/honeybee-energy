#! /usr/bin/env sh
set -e

error_help="Usage: $0 CONTAINER_NAME TAG [REMOVE_DOWNLOADS=false|true]"

export CONTAINER_NAME="${1:?$error_help}"
export TAG="${2:?$error_help}"

# Get OpenStudio

export OPENSTUDIO_VERSION='3.2.0'
export OPENSTUDIO_DOWNLOAD_URL='https://github.com/NREL/OpenStudio/releases/download/v3.2.0/OpenStudio-3.2.0+e11f0a08b2-Ubuntu-20.04.tar.gz'
export OPENSTUDIO_TAR_FILENAME='openstudio.tar.gz'
export OPENSTUDIO_FILENAME='openstudio'

curl -SL -o ${OPENSTUDIO_TAR_FILENAME} ${OPENSTUDIO_DOWNLOAD_URL}
tar zxvf ${OPENSTUDIO_TAR_FILENAME}
mv OpenStudio-*-Linux/ ${OPENSTUDIO_FILENAME}

# Get the gem

export HONEYBEE_OPENSTUDIO_GEM_VERSION='2.17.0'
export HONEYBEE_OPENSTUDIO_GEM_URL="https://github.com/ladybug-tools/honeybee-openstudio-gem/archive/v${HONEYBEE_OPENSTUDIO_GEM_VERSION}.tar.gz"
export HONEYBEE_OPENSTUDIO_GEM_TAR='honeybee-openstudio-gem.tar.gz'
export HONEYBEE_GEM_FILENAME='honeybee-gem'

curl -SL -o ${HONEYBEE_OPENSTUDIO_GEM_TAR} ${HONEYBEE_OPENSTUDIO_GEM_URL}
tar zxvf ${HONEYBEE_OPENSTUDIO_GEM_TAR}
mv honeybee-openstudio-gem-*/ ${HONEYBEE_GEM_FILENAME}

docker build . \
  -t $CONTAINER_NAME:$TAG \
  --build-arg OPENSTUDIO_VERSION=${OPENSTUDIO_VERSION} \
  --build-arg OPENSTUDIO_FILENAME=${OPENSTUDIO_FILENAME} \
  --build-arg HONEYBEE_GEM_FILENAME=${HONEYBEE_GEM_FILENAME}

if [[ "${3}" == 'true' ]]; then
    rm -rf openstudio* honeybee-*
fi
