#!/usr/bin/env bash

which python
for i in {1..30}; do
  echo "Run #$i"
  netsquid/bin/python3.10 bo2sweep.py >> bo2sweep.txt
  echo "Run #$i Complete"
done
