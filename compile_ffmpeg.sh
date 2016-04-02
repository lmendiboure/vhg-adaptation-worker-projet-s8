#!/bin/bash
BUILD="$(pwd)/build"
mkdir $BUILD
PREFIX="/usr/local/"
BINDIR="/usr/local/bin"
mkdir -p $PREFIX

#echo "export PATH=$PATH:/usr/local/ffmpeg/bin" >> .bashrc

apt-get update
apt-get -y install autoconf automake build-essential libass-dev libfreetype6-dev libgpac-dev \
  libsdl1.2-dev libtheora-dev libtool libva-dev libvdpau-dev libvorbis-dev libx11-dev \
  libxext-dev libxfixes-dev pkg-config texi2html zlib1g-dev yasm libx264-dev libfdk-aac-dev libmp3lame-dev libopus-dev libvpx-dev
mkdir ~/ffmpeg_sources

cd $BUILD
git clone  https://github.com/gpac/gpac --branch v0.5.2 --single-branch

 git clone https://github.com/FFmpeg/FFmpeg.git --branch release/2.6 --single-branch
cd FFmpeg 


PKG_CONFIG_PATH="$PREFIX/lib/pkgconfig" 
./configure \
  --prefix="$PREFIX" \
  --extra-cflags="-I$PREFIX/include" \
  --extra-ldflags="-L$PREFIX/lib" \
  --bindir=$BINDIR \
  --enable-gpl \
  --enable-pic \
  --enable-libass \
  --enable-libfdk-aac \
  --enable-libfreetype \
  --enable-libmp3lame \
  --enable-libopus \
  --enable-libtheora \
  --enable-libvorbis \
  --enable-libvpx \
  --enable-libx264 \
  --enable-nonfree

make
make install
make distclean
