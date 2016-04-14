#!/bin/bash
#Script for Ubuntu 14.04

#Install RabbitMQ for Celery, Then Celery and MediaInfo wrapper for python
sudo apt-get -y install rabbitmq-server python-pip mediainfo python-lxml python-dev wget yasm nasm
sudo pip install celery pymediainfo

#Compile Manually MP4Box from GPAC project
chmod 777 compile_MP4Box.sh
sudo ./compile_MP4Box.sh

#Compile FFmpeg
chmod 777 compile_ffmpeg.sh
sudo ./compile_ffmpeg.sh


chmod 777 start.sh
chmod 777 MyCommand.txt

# Download and compile OpenH264 to use h264enc (encoding the videos with openh264)

cd adaptation
git clone https://github.com/lmendiboure/openh264-projetS8.git --branch dev-projetS8
cd openh264-projetS8
make
cd ..


# Download and compile MD-OpenH264 to use the postProcessor (creator of descriptions)
git clone https://github.com/Jobq/MD-openh264.git --branch dev-projetS8-feature
cd MD-openh264/
make
cd ..
