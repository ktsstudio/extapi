# 0.1.7
* change licenses to Apache 2.0

# 0.1.6
* moved to github

# 0.1.5
* removed unnecessary `asyncio.sleep` after the last retry in `RetryableExecutor.execute`

# 0.1.4
* removed opentelemetry-sdk from dependencies

# 0.1.3
* simplify storing cached Response data

# 0.1.2
* added `auto_read_body` to request and backends in order to automatically read response body so that all retry logic could happen in case of errors

# 0.1.1
* Response: added `original` proxy property

# 0.1.0

* Initial release
