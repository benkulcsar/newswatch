#!/bin/bash

start_date=$(date -d "$1" +%s)
end_date=$(date -d "$2" +%s)
lambda_function_name=$3
bucket_name=$4
prefix=$5

current_date=$start_date

while [[ $current_date -le $end_date ]]; do
    date_string=$(date -d @$current_date +%Y-%m-%d)
    year=$(date -d "$date_string" +%Y)
    month=$(date -d "$date_string" +%m)
    day=$(date -d "$date_string" +%d)

    for hour in {00..23}; do
        key="${prefix}/year=${year}/month=${month}/day=${day}/hour=${hour}.json"

        echo $key

        aws lambda invoke \
            --function-name "$lambda_function_name" \
            --invocation-type Event \
            --payload "{\"detail\":{\"bucket\":{\"name\":\"${bucket_name}\"},\"object\":{\"key\":\"${key}\"}}}" \
            --cli-binary-format raw-in-base64-out \
            /dev/stdout
    done

    current_date=$((current_date + 86400))  # Adding 86400 seconds (1 day) to the current date
done
