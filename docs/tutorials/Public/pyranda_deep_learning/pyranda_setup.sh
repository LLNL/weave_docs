#!/bin/bash

python3 -m venv --system-site-packages pyranda_venv
source pyranda_venv/bin/activate
pip install --upgrade pip
git clone https://github.com/LLNL/pyranda.git
cd pyranda
pip install .

echo "Setup complete!"
