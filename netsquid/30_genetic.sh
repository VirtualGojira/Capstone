#!/usr/bin/env bash

which python
rm -rf geneticparallelsweep_results.txt
for i in {1..30}; do
  echo "Run #$i"
  netsquid/bin/python3.10 geneticparallelsweep.py >> geneticparallelsweep_results.txt
  echo "Run #$i Complete"
done
