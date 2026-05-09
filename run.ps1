param (
    [string]$Config = "../config.json"
)

uv run python make_anniversary_video.py --config $Config
