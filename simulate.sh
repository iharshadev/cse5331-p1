#!/usr/bin/env bash
for i in $(ls -1 inputs/input*.txt); do
echo -e "\n\nInput file: $i"
python main.py wound-wait ${i}
done
