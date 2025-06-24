# C/C++ Runtime Environment
FROM gcc:latest

# Set working directory
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    nano \
    cmake \
    make \
    gdb \
    valgrind \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -s /bin/bash coderunner
USER coderunner

# Set environment variables
ENV CC=gcc
ENV CXX=g++

# Default command
CMD ["/bin/bash"]

