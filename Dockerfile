FROM python:3.11-slim-bookworm

# Build dependencies for liboqs
RUN apt-get update && apt-get install -y \
    cmake ninja-build gcc g++ git libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Build liboqs from source (reproducible build)
RUN git clone --depth 1 https://github.com/open-quantum-safe/liboqs.git /tmp/liboqs \
    && cd /tmp/liboqs && mkdir build && cd build \
    && cmake -GNinja -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON .. \
    && ninja && ninja install && ldconfig \
    && rm -rf /tmp/liboqs

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
