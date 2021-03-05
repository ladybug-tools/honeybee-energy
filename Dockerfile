FROM python:3.7-slim

LABEL maintainer="Ladybug Tools" email="info@ladybug.tools"

ARG OPENSTUDIO_VERSION
ARG OPENSTUDIO_FILENAME
ARG HONEYBEE_GEM_FILENAME

ENV HOME_PATH='/home/ladybugbot'
ENV LBT_PATH="${HOME_PATH}/ladybug_tools"
ENV LIBRARY_PATH="${HOME_PATH}/lib"
ENV LOCAL_OPENSTUDIO_PATH="${LBT_PATH}/openstudio"
ENV RUN_PATH="${HOME_PATH}/run"
ENV SIM_PATH="${RUN_PATH}/simulation"
ENV PATH="${HOME_PATH}/.local/bin:${PATH}"

# Create non-root user
RUN adduser ladybugbot --uid 1000 --disabled-password --gecos ""
USER ladybugbot
WORKDIR ${HOME_PATH}
RUN mkdir -p ${LOCAL_OPENSTUDIO_PATH} \
    && touch ${LBT_PATH}/config.json \
    && mkdir -p ${SIM_PATH}

# Expects an untarred OpenStudio download in the build context
COPY ${OPENSTUDIO_FILENAME}/usr/local/openstudio-${OPENSTUDIO_VERSION}/EnergyPlus \
    ${LOCAL_OPENSTUDIO_PATH}/EnergyPlus

COPY ${OPENSTUDIO_FILENAME}/usr/local/openstudio-${OPENSTUDIO_VERSION}/bin \
    ${LOCAL_OPENSTUDIO_PATH}/bin

# Add honeybee-openstudio-gem lib to ladybug_tools folder
# Expects an untarred honeybee-openstudio-gem in the build context
# https://github.com/ladybug-tools/honeybee-openstudio-gem
COPY ${HONEYBEE_GEM_FILENAME} \
    ${LBT_PATH}/resources/measures/honeybee_openstudio_gem

# Install honeybee-energy
COPY honeybee_energy ${LIBRARY_PATH}/honeybee_energy
COPY .git ${LIBRARY_PATH}/.git
COPY setup.py ${LIBRARY_PATH}
COPY setup.cfg ${LIBRARY_PATH}
COPY requirements.txt ${LIBRARY_PATH}
COPY README.md ${LIBRARY_PATH}
COPY LICENSE ${LIBRARY_PATH}

USER root
RUN apt-get update \
    && apt-get -y install --no-install-recommends git \
    # EnergyPlus dynamically links to libx11
    && apt-get -y install libx11-6 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install --no-cache-dir setuptools wheel \
    && pip3 install --no-cache-dir ${LIBRARY_PATH}[standards] \
    && apt-get -y --purge remove git \
    && apt-get -y clean \
    && apt-get -y autoremove \
    && rm -rf ${LIBRARY_PATH}/.git \
    && chown -R ladybugbot ${HOME_PATH}

USER ladybugbot
# Set working directory
WORKDIR ${RUN_PATH}
