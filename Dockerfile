FROM nvidia/cuda:11.3.1-devel-ubuntu20.04

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV CUDNN_VERSION 8.2.1.32
ENV FORCE_CUDA="1"
ENV CUDA_CACHE_DISABLE="1"

RUN rm /etc/apt/sources.list.d/cuda.list || true
RUN rm /etc/apt/sources.list.d/nvidia-ml.list || true
RUN apt-key del 7fa2af80
RUN apt-get update && apt-get install -y --no-install-recommends wget
RUN wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-keyring_1.0-1_all.deb
RUN dpkg -i cuda-keyring_1.0-1_all.deb

ARG DEBIAN_FRONTEND=noninteractive
RUN DEBIAN_FRONTEND="noninteractive" apt-get update && apt-get -y install tzdata

ENV TORCH_CUDA_ARCH_LIST="Turing"
ENV TORCH_NVCC_FLAGS="-Xfatbin -compress-all"

LABEL com.nvidia.cudnn.version="${CUDNN_VERSION}"

RUN apt-get update && apt-get install -y --no-install-recommends \
    libcudnn8=$CUDNN_VERSION-1+cuda11.3 \
    curl \
    software-properties-common \
    && apt-mark hold libcudnn8 && \
    rm -rf /var/lib/apt/lists/*

ENV TZ=Europe/London
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt update && apt install --no-install-recommends -y \
    build-essential \
    gcc \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common \
    cmake \
    protobuf-compiler

RUN add-apt-repository 'ppa:deadsnakes/ppa' -y
RUN apt update && apt install -y --no-install-recommends \
    python3.8 \
    python3.8-dev \
    python3-pip \
    python3-all-dev \
    libasound-dev \
    portaudio19-dev \
    libportaudio2 \
    libportaudiocpp0

RUN apt update && \
    apt install -y --no-install-recommends \
    libsqlite3-0 \
    ffmpeg \
    x264\
    libx264-dev

RUN apt update && apt install -y --no-install-recommends \
    gcc \
    gettext \
    libpq-dev \
    sqlite3 \
    wget \
    libreoffice \
    libreoffice-java-common \
    openjdk-11-jre-headless \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /usr/src/app/
WORKDIR /usr/src/app/
RUN cd /usr/src/app/

COPY requirements.txt ./requirements.txt

RUN python3.8 -m pip install urllib3 requests praat-parselmouth==0.4.3 --default-timeout 10000
RUN python3.8 -m pip install torch==1.12.1+cu113 torchvision==0.13.1+cu113 torchaudio==0.12.1 --extra-index-url https://download.pytorch.org/whl/cu113 --default-timeout 10000
RUN python3.8 -m pip install -r requirements.txt --default-timeout 10000

COPY . /usr/src/app/

RUN python3.8 manage.py makemigrations
RUN python3.8 manage.py migrate
CMD ["python3.8", "manage.py", "runserver", "0.0.0.0:8000"]
