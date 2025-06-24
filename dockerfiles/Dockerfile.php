# PHP Runtime Environment
FROM php:8.2-cli

# Set working directory
WORKDIR /workspace

# Install system dependencies and PHP extensions
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    nano \
    zip \
    unzip \
    libzip-dev \
    && docker-php-ext-install zip pdo pdo_mysql \
    && rm -rf /var/lib/apt/lists/*

# Install Composer
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

# Create a non-root user
RUN useradd -m -s /bin/bash coderunner
USER coderunner

# Set environment variables
ENV PATH=/workspace/vendor/bin:$PATH

# Default command
CMD ["/bin/bash"]

