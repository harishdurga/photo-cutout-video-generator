.PHONY: setup run

CONFIG ?= ../config.json

setup:
	uv sync

run:
	uv run python main.py --config $(CONFIG)
