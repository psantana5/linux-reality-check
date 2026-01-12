# Docker container for isolated testing

FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    linux-tools-generic \
    linux-tools-common \
    python3 \
    python3-pip \
    stress-ng \
    && rm -rf /var/lib/apt/lists/*

# Set up workspace
WORKDIR /lrc

# Copy project files
COPY core/ ./core/
COPY scenarios/ ./scenarios/
COPY analyze/ ./analyze/
COPY report/ ./report/
COPY docs/ ./docs/
COPY scripts/ ./scripts/
COPY README.md ./

# Build
RUN cd core && make && cd ../scenarios && make

# Default command
CMD ["/bin/bash"]
