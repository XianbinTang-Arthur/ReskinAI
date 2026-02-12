#!/usr/bin/env bash
set -euo pipefail

echo "[bootstrap] Updating packages..."
sudo dnf update -y

echo "[bootstrap] Installing Docker, Git, and Compose plugin..."
sudo dnf install -y docker git docker-compose-plugin

echo "[bootstrap] Enabling Docker service..."
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user

echo "[bootstrap] Creating app directory..."
sudo mkdir -p /home/ec2-user/ReskinAI
sudo chown -R ec2-user:ec2-user /home/ec2-user/ReskinAI

echo "[bootstrap] Done. Re-login required for docker group to apply."
