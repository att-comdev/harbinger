FROM bitnami/minideb:jessie

LABEL maintainer "Oded Le'Sage <ol7435@att.com>"

#add necessary environment variables
ENV HARBINGER_DIR /opt/harbinger

# install system packages
RUN apt-get update && install_packages sudo ncurses-bin nano git curl \
    wget gcc netbase vim tree less qemu-utils kpartx

# install system python packages
RUN install_packages python-dev python-pip

# upgrade python install packages
RUN pip install -U pip pbr setuptools

# install python packages
RUN pip install virtualenv tox

# install harbinger
COPY . $HARBINGER_DIR-src
RUN pip install -e $HARBINGER_DIR-src/

# create venvs directory
RUN mkdir -p $HARBINGER_DIR/venvs

# create frameworks directory
WORKDIR $HARBINGER_DIR/frameworks

# install shaker
RUN virtualenv $HARBINGER_DIR/venvs/shaker
RUN git clone https://github.com/openstack/shaker.git
RUN /bin/bash -c "source $HARBINGER_DIR/venvs/shaker/bin/activate; pip install -e shaker/"

# install yardstick
RUN virtualenv $HARBINGER_DIR/venvs/yardstick
RUN git clone https://github.com/opnfv/yardstick.git
RUN /bin/bash -c "source $HARBINGER_DIR/venvs/yardstick/bin/activate; pip install -e yardstick/; \
    pip install -r yardstick/requirements.txt"

# patch to allow the yardstick image to build correctly
RUN sed -i 's|kpartx -av|kpartx -avs|g' $HARBINGER_DIR/frameworks/yardstick/tools/yardstick-img-modify

# add convenience to harbinger
RUN echo "alias hrb='harbinger'" >> ~/.bashrc

WORKDIR /home/harbinger

CMD ["/bin/bash"]
