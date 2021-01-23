FROM python:3.7

LABEL maintainer="Ladybug Tools" email="info@ladybug.tools"

# Create non-root user
RUN adduser ladybugbot --uid 1000
USER ladybugbot
WORKDIR /home/ladybugbot
RUN mkdir ladybug_tools && touch ladybug_tools/config.json

# Install Open Studio
ENV OPENSTUDIO_VERSION=3.1.0
ENV OPENSTUDIO_FILENAME=OpenStudio-3.1.0+e165090621-Linux
ENV OPENSTUDIO_DOWNLOAD_URL=https://openstudio-ci-builds.s3-us-west-2.amazonaws.com/3.1.0/OpenStudio-3.1.0%2Be165090621-Linux.tar.gz
RUN mkdir ladybug_tools/openstudio/ \
    && curl -SL -o openstudio.tar.gz $OPENSTUDIO_DOWNLOAD_URL \
    && tar zxvf openstudio.tar.gz \
    && mv $OPENSTUDIO_FILENAME/usr/local/openstudio-$OPENSTUDIO_VERSION/EnergyPlus ladybug_tools/openstudio/EnergyPlus \
    && mv $OPENSTUDIO_FILENAME/usr/local/openstudio-$OPENSTUDIO_VERSION/bin ladybug_tools/openstudio/bin \
    && rm -r $OPENSTUDIO_FILENAME \
    && rm openstudio.tar.gz


# Add honeybee-openstudio-gem lib to ladybug_tools folder
ENV HONEYBEE_OPENSTUDIO_GEM_VERSION=2.11.1
RUN mkdir -p ladybug_tools/resources/measures/honeybee_openstudio_gem \
    && curl -SL -o honeybee-openstudio-gem.tar.gz https://github.com/ladybug-tools/honeybee-openstudio-gem/archive/v$HONEYBEE_OPENSTUDIO_GEM_VERSION.tar.gz \
    && tar zxvf honeybee-openstudio-gem.tar.gz \
    && mv honeybee-openstudio-gem-$HONEYBEE_OPENSTUDIO_GEM_VERSION/lib ladybug_tools/resources/measures/honeybee_openstudio_gem \
    && rm -r honeybee-openstudio-gem-$HONEYBEE_OPENSTUDIO_GEM_VERSION \
    && rm honeybee-openstudio-gem.tar.gz


# Install honeybee-energy cli
ENV PATH="/home/ladybugbot/.local/bin:${PATH}"
COPY . honeybee-energy
RUN pip3 install setuptools wheel\
    && pip3 install ./honeybee-energy[cli]

# Set up working directory
RUN mkdir -p /home/ladybugbot/run/simulation
WORKDIR /home/ladybugbot/run
