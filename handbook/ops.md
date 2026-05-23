# Operations

This manual is for platform operators and DevOps engineers responsible for deploying, monitoring, and maintaining the AI Platform. Use it to understand how to run the service in production, what to watch in dashboards, and how to respond to incidents.

## Overview

This section describes the platform's runtime architecture — the FastAPI backend, the PydanticAI agent layer, and the NestJS backend it calls — and the responsibilities of an operator across deploy, monitor, and incident-response cycles.

## Prerequisites

This section lists the infrastructure requirements: Python 3.11+, PostgreSQL 14+, environment variables, and any third-party AI provider keys that must be present before the service starts.

## Core procedures

This section holds the numbered runbooks operators follow most often: deploying a new release, rolling back, rotating secrets, and scaling the service under load.

## Reference

This section documents environment variable definitions, service health endpoints, log formats, and the expected NestJS backend contract the platform depends on.

## Troubleshooting

This section covers production failure modes — agent timeouts, database connection errors, NestJS API contract breaks — and the diagnostic steps and remediation actions for each.

## Changelog

This section records infrastructure and operational changes across platform releases.
