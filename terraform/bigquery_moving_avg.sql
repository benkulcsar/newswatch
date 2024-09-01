MERGE `${project}.looker.word-frequencies-ma-${env}${optional_suffix}` MA
USING (
  SELECT
    timestamp,
    word,
    cast(avg(frequency) over (PARTITION BY word ORDER BY timestamp ROWS BETWEEN ${window_hours} PRECEDING AND CURRENT ROW ) as int) as frequency
  FROM `${project}.looker.word-frequencies-partitioned-${env}${optional_suffix}`
  WHERE timestamp > TIMESTAMP_ADD(TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), DAY), INTERVAL -${lookback_days} DAY)
) LIVE
ON MA.timestamp=LIVE.timestamp
WHEN NOT MATCHED THEN
  INSERT(timestamp, word, frequency)
  VALUES(timestamp, word, frequency)
