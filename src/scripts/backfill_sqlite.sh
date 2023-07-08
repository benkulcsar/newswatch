#!/bin/bash

export PYTHONPATH='./src'
python ./src/scripts/_backfill.py "$@"
