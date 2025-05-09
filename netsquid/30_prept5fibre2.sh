#!/usr/bin/env bash

source "./netsquid/bin/activate"
which python
for i in {1..30}; do
  echo "Run #$i"
  netsquid/bin/python3.10 prept5fibre2.py >> SMF-28_ULL_S+_results.txt
done
