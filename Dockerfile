FROM python:3.11-slim

WORKDIR /app/bot

COPY ./requirements.txt ./
RUN python -m pip install --upgrade pip setuptools wheel build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    automake \
    libtool \
    libffi-dev \
    libgmp-dev \
    python3-dev \
    libssl-dev \
    git \
    curl \
    ca-certificates

RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
RUN export PATH="/root/.cargo/bin:${PATH}"
RUN pip install --no-cache-dir -r requirements.txt

COPY ./ ./

CMD ["python", "run.py"]
