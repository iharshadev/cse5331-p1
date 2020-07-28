#!/usr/bin/env bash
rm -rf outputs/*
mkdir -p outputs/{wound-wait,wait-die}
for method in {"wound-wait","wait-die"}; do
    for input in $(ls -1 inputs/input*.txt); do
        output="outputs/$method/$(sed 's/inputs\///g;s/input/output/g' <<< ${input})"
        echo -e "\nInput file: $input, Output also saved to: ${output}"
        python main.py ${method} ${input} | tee ${output}
    done
done
