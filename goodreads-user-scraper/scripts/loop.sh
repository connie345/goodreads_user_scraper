#!/usr/bin/env bash

python -m scraper --user_id 35 --output_dir 35
for i in {1..1000000}
do
    output_file="goodreads-data/"$i
    python -m scraper --user_id $i --output_dir $output_file
done