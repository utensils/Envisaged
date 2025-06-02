# !/usr/bin/make -f

SHELL := /usr/bin/env bash
IMAGE_NAME ?= envisaged
DOCKER_TAG ?= utensils/$(IMAGE_NAME):latest
# Example GIT_URL for testing, user should override or set as env var for docker run
TEST_GIT_URL ?= https://github.com/git-fixtures/basic.git

# Default target
.PHONY: default
default: build

# Build the Docker image
.PHONY: build
build:
	sudo docker build -t $(DOCKER_TAG) .

# Run the Docker image for local testing
# Mounts ./test_output (created if not exists) to /visualization in the container
# Uses a test Git URL.
.PHONY: run
run:
	mkdir -p ./test_output/video ./test_output/git_repo ./test_output/avatars # HTML dir no longer needed
	sudo docker run --rm \
		-v $(shell pwd)/test_output:/visualization \
		-e GIT_URL=$(TEST_GIT_URL) \
		-e GOURCE_TITLE="Test Run" \
		-e TEMPLATE="border" \
		$(DOCKER_TAG)

# Clean up local test output
.PHONY: clean
clean:
	rm -rf ./test_output

# Target to show help or available targets (optional)
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  build    - Build the Docker image as $(DOCKER_TAG)"
	@echo "  run      - Run the Docker image with a test Git repository, outputting to ./test_output"
	@echo "  clean    - Remove the ./test_output directory"
