# Go Runtime Environment
FROM golang:1.21-alpine

# Set working directory
WORKDIR /workspace

# Install system dependencies
RUN apk add --no-cache \
    git \
    curl \
    vim \
    nano \
    bash

# Create a non-root user
RUN adduser -D -s /bin/bash coderunner
USER coderunner

# Set environment variables
ENV GOPATH=/workspace
ENV GOCACHE=/tmp/.cache/go-build
ENV PATH=$GOPATH/bin:$PATH

# Default command
CMD ["/bin/bash"]

