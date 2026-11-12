#!/bin/bash
set -e
pnpm install --frozen-lockfile
pip install -r artifacts/api-server-python/requirements.txt
