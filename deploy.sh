#!/bin/sh

if [ -n "$1" ]
then
  NEXT_RELEASE_VERSION=$1
else
  echo "A release version must be supplied"
  exit 1
fi


echo "PyPi Deployment..."
echo "Building distribution"
python setup.py sdist bdist_wheel
echo "Pushing new version to PyPi"
twine upload dist/* -u $PYPI_USERNAME -p $PYPI_PASSWORD


echo "Docker Deployment..."
echo "Login to Docker"
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
CONTAINER_NAME="ladybugtools/honeybee-energy"

# Get OpenStudio

export OPENSTUDIO_VERSION='3.1.0'
export OPENSTUDIO_DOWNLOAD_URL='https://openstudio-ci-builds.s3-us-west-2.amazonaws.com/3.1.0/OpenStudio-3.1.0%2Be165090621-Linux.tar.gz'
export OPENSTUDIO_TAR_FILENAME='openstudio.tar.gz'
export OPENSTUDIO_FILENAME='openstudio'

curl -SL -o ${OPENSTUDIO_TAR_FILENAME} ${OPENSTUDIO_DOWNLOAD_URL}
tar zxvf ${OPENSTUDIO_TAR_FILENAME}
mv OpenStudio-*-Linux/ ${OPENSTUDIO_FILENAME}

# Get the gem

export HONEYBEE_OPENSTUDIO_GEM_VERSION='2.11.1'
export HONEYBEE_OPENSTUDIO_GEM_URL="https://github.com/ladybug-tools/honeybee-openstudio-gem/archive/v${HONEYBEE_OPENSTUDIO_GEM_VERSION}.tar.gz"
export HONEYBEE_OPENSTUDIO_GEM_TAR='honeybee-openstudio-gem.tar.gz'
export HONEYBEE_GEM_FILENAME='honeybee-gem'

curl -SL -o ${HONEYBEE_OPENSTUDIO_GEM_TAR} ${HONEYBEE_OPENSTUDIO_GEM_URL}
tar zxvf ${HONEYBEE_OPENSTUDIO_GEM_TAR}
mv honeybee-openstudio-gem-*/ ${HONEYBEE_GEM_FILENAME}

docker build . \
  -t $CONTAINER_NAME:$NEXT_RELEASE_VERSION \
  --build-arg OPENSTUDIO_VERSION=${OPENSTUDIO_VERSION} \
  --build-arg OPENSTUDIO_FILENAME=${OPENSTUDIO_FILENAME} \
  --build-arg HONEYBEE_GEM_FILENAME=${HONEYBEE_GEM_FILENAME}

docker tag $CONTAINER_NAME:$NEXT_RELEASE_VERSION $CONTAINER_NAME:latest

docker push $CONTAINER_NAME:latest
docker push $CONTAINER_NAME:$NEXT_RELEASE_VERSION
