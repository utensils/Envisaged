# Define your target architectures
ARCHS ?= linux/amd64,linux/386,linux/arm64,linux/arm/v7

# Docker image information
REPO_NAMESPACE ?= utensils
IMAGE_NAME     ?= envisaged
VCS_REF        := $(shell git rev-parse --short HEAD)
BUILD_DATE     := $(shell date -u +"%Y-%m-%dT%H:%M:%SZ")

# Multi-architecture build, tagged with the VCS ref, pushed to the registry
.PHONY: build
build: setup-builder
	docker buildx build \
		--platform $(ARCHS) \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--tag $(REPO_NAMESPACE)/$(IMAGE_NAME):$(VCS_REF) \
		--push .

# Single-architecture local build using standard docker build
.PHONY: build-local
build-local:
	docker buildx build \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--tag $(REPO_NAMESPACE)/$(IMAGE_NAME):$(VCS_REF) \
		--load .

# Ensure Buildx builder exists
.PHONY: setup-builder
setup-builder:
	@if ! docker buildx inspect multiarch-builder >/dev/null 2>&1; then \
		docker buildx create --use --name multiarch-builder; \
		docker buildx inspect multiarch-builder --bootstrap; \
	fi

# Clean up the builder instance
.PHONY: clean
clean:
	docker buildx rm multiarch-builder || true
