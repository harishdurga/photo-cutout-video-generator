.PHONY: setup run

CONFIG ?= ../config.json

setup:
	uv sync

run:
	uv run python make_anniversary_video.py --config $(CONFIG)
