#!/bin/bash

echo "激活conda环境并运行Ground Truth诊断..."
echo "=================================================="

source ~/.bashrc
conda activate projectwcsnet
python check_ground_truth.py

