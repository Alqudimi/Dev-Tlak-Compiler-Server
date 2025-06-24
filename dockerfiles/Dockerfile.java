# Java Runtime Environment
FROM openjdk:17-slim

# Set working directory
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    nano \
    maven \
    gradle \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -s /bin/bash coderunner
USER coderunner

# Set environment variables
ENV JAVA_HOME=/usr/local/openjdk-17
ENV PATH=$JAVA_HOME/bin:$PATH
ENV CLASSPATH=/workspace

# Default command
CMD ["/bin/bash"]

