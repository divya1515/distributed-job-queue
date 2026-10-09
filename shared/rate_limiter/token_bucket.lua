-- KEYS[1]: The rate limit key (e.g., "rate_limit:127.0.0.1")
-- ARGV[1]: Max bucket capacity (burst size)
-- ARGV[2]: Refill rate (tokens per second)
-- ARGV[3]: Current timestamp (seconds)
-- ARGV[4]: Requested tokens (usually 1)

local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

-- Retrieve existing bucket state
local data = redis.call("HMGET", key, "tokens", "last_updated")
local tokens = tonumber(data[1])
local last_updated = tonumber(data[2])

if not tokens then
    -- First request: Initialize bucket to full capacity
    tokens = capacity
    last_updated = now
else
    -- Calculate refilled tokens based on time elapsed
    local elapsed = math.max(0, now - last_updated)
    tokens = math.min(capacity, tokens + (elapsed * refill_rate))
    last_updated = now
end

-- Check if enough tokens exist
if tokens >= requested then
    tokens = tokens - requested
    redis.call("HMSET", key, "tokens", tokens, "last_updated", last_updated)
    -- Set TTL slightly longer than it takes to completely refill the bucket
    local ttl = math.ceil(capacity / refill_rate)
    redis.call("EXPIRE", key, ttl)
    return 1 -- Allowed
else
    -- Reject, preserve the refilled token state
    redis.call("HMSET", key, "tokens", tokens, "last_updated", last_updated)
    return 0 -- Rate limited
end
