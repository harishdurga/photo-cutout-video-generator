param (
    [string]$Config = "../config.json"
)

uv run python main.py --config $Config
