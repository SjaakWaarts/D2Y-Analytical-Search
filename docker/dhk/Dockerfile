FROM centos:7

# Create Python layer
RUN yum install -y epel-release
RUN yum install wget

# set working directory
RUN wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-7.7.0-x86_64.rpm
RUN wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-7.7.0-x86_64.rpm.sha512
#RUN shasum -a 512 -c elasticsearch-7.7.0-x86_64.rpm.sha512
RUN rpm --install elasticsearch-7.7.0-x86_64.rpm
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
