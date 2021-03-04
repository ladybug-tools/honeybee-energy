FROM python:3.7-slim

LABEL maintainer="Ladybug Tools" email="info@ladybug.tools"

ARG OPENSTUDIO_VERSION
ARG OPENSTUDIO_FILENAME

ENV HOME_PATH='/home/ladybugbot'
ENV LBT_PATH="${HOME_PATH}/ladybug_tools"
ENV LOCAL_OPENSTUDIO_PATH="${LBT_PATH}/openstudio"

# Create non-root user
RUN adduser ladybugbot --uid 1000 --disabled-password --gecos ""
USER ladybugbot
WORKDIR ${HOME_PATH}
RUN mkdir -p ${LOCAL_OPENSTUDIO_PATH} && touch ${LBT_PATH}/config.json

# keep
COPY ${OPENSTUDIO_FILENAME}/usr/local/openstudio-${OPENSTUDIO_VERSION}/EnergyPlus \
    ${LOCAL_OPENSTUDIO_PATH}/EnergyPlus

COPY ${OPENSTUDIO_FILENAME}/usr/local/openstudio-${OPENSTUDIO_VERSION}/bin \
    ${LOCAL_OPENSTUDIO_PATH}/bin


# Add honeybee-openstudio-gem lib to ladybug_tools folder
ENV HONEYBEE_OPENSTUDIO_GEM_VERSION=2.11.1
RUN mkdir -p ladybug_tools/resources/measures/honeybee_openstudio_gem \
    && curl -SL -o honeybee-openstudio-gem.tar.gz https://github.com/ladybug-tools/honeybee-openstudio-gem/archive/v$HONEYBEE_OPENSTUDIO_GEM_VERSION.tar.gz \
    && tar zxvf honeybee-openstudio-gem.tar.gz \
    && mv honeybee-openstudio-gem-$HONEYBEE_OPENSTUDIO_GEM_VERSION/lib ladybug_tools/resources/measures/honeybee_openstudio_gem \
    && rm -r honeybee-openstudio-gem-$HONEYBEE_OPENSTUDIO_GEM_VERSION \
    && rm honeybee-openstudio-gem.tar.gz


# Install honeybee-energy
ENV PATH="/home/ladybugbot/.local/bin:${PATH}"
COPY . honeybee-energy
RUN pip3 install setuptools wheel\
    && pip3 install ./honeybee-energy[standards]

# Set up working directory
RUN mkdir -p /home/ladybugbot/run/simulation
WORKDIR /home/ladybugbot/run
