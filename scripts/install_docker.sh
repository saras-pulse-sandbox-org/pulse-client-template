#!/bin/bash

# Enable debug mode
set -x

for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do
    sudo apt-get remove -y $pkg || true
done

sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

# Create keyrings directory
sudo install -m 0755 -d /etc/apt/keyrings

# Download and import the key with verification
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Explicitly download and add the GPG key
curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/docker.gpg > /dev/null
sudo apt-key add /etc/apt/trusted.gpg.d/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update

sudo apt-get install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin

sudo groupadd docker || true
sudo usermod -aG docker $USER

sudo systemctl start docker
sudo systemctl enable docker

sudo docker version
sudo docker run hello-world

# Disable debug mode
set +x