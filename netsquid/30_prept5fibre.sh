#!/usr/bin/env bash

source "./netsquid/bin/activate"
which python
for i in {1..30}; do
  echo "Run #$i"
  netsquid/bin/python3.10 prept5fibre.py >> SMF-28_ULL_Ulta_Bend_results.txt
done
