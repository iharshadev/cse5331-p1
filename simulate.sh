#!/usr/bin/env bash
for method in {"wound-wait","wait-die"}; do
    for i in $(ls -1 inputs/input*.txt); do
        echo -e "Input file: $i"
        python main.py $method ${i}
        echo -e "\n"
    done
done
