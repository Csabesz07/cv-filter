# Ranking Events API Documentation

## Overview

The Ranking Events API provides detailed tracking and querying capabilities for ranking run operations. This endpoint is specifically designed for monitoring, debugging, and auditing ranking algorithm executions.

## Endpoint

```
GET /api/audit/ranking/
```

**Authentication Required:** Yes (JWT Bearer token)

## Features

- Query all ranking-related audit events
- Filter by specific ranking run ID
- Filter by event type
- Automatic statistics calculation for individual runs
- Support for pagination via limit parameter

## Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `run_id` | UUID | No | - | Filter events for a specific ranking run |
| `event_type` | String | No | - | Filter by event type (e.g., "ranking.run.started") |
| `limit` | Integer | No | 100 | Maximum number of results (max: 1000) |

## Response Format

```json
{
  "count": 3,
  "results": [
    {
      "id": "uuid",
      "organization": "uuid",
      "organization_name": "string",
      "actor_user": "uuid",
      "actor_username": "string",
      "severity": "log",
      "event_type": "ranking.run.started",
      "entity_type": "ranking_run",
      "entity_id": "uuid",
      "description": "string",
      "metadata": {
        "run_id": "uuid",
        "criteria": [...],
        "has_bias_config": false
      },
      "created_at": "2026-01-14T12:00:00Z"
    }
  ],
  "statistics": {
    "total_events": 3,
    "event_types": {
      "ranking.run.started": 1,
      "ranking.run.completed": 1
    },
    "has_completion": true,
    "has_failure": false,
    "candidates_evaluated": 50,
    "scores_created": 50,
    "total_duration_seconds": 2.5,
    "score_statistics": {
      "mean": 0.75,
      "median": 0.78,
      "min": 0.12,
      "max": 0.98
    }
  }
}
```

## Event Types

The following ranking event types are tracked:

### 1. `ranking.run.started`
Logged when a ranking run begins.

**Metadata:**
- `run_id`: Ranking run UUID
- `criteria`: Array of ranking criteria
- `has_bias_config`: Boolean indicating bias mitigation
- `max_candidates`: Maximum candidates to evaluate

### 2. `ranking.candidates.loaded`
Logged after candidates are loaded for evaluation.

**Metadata:**
- `run_id`: Ranking run UUID
- `candidates_count`: Number of candidates loaded
- `load_duration_seconds`: Time to load candidates

### 3. `ranking.scoring.completed`
Logged after all candidates are scored.

**Metadata:**
- `run_id`: Ranking run UUID
- `candidates_scored`: Number of candidates scored
- `scoring_duration_seconds`: Time to score all candidates
- `average_score`: Mean score across all candidates

### 4. `ranking.run.completed`
Logged when ranking run completes successfully.

**Metadata:**
- `run_id`: Ranking run UUID
- `candidates_evaluated`: Total candidates evaluated
- `scores_created`: Total scores created
- `total_duration_seconds`: Total execution time
- `score_statistics`: Statistical summary of scores
  - `mean`: Average score
  - `median`: Median score
  - `min`: Minimum score
  - `max`: Maximum score
  - `std_dev`: Standard deviation

### 5. `ranking.run.failed`
Logged when ranking run fails.

**Metadata:**
- `run_id`: Ranking run UUID
- `error`: Error message
- `error_type`: Type of error (e.g., "ValueError")
- `partial_results`: Boolean indicating if partial results exist

### 6. `ranking.created`
Logged when a new ranking run is created via API.

**Metadata:**
- `criteria_count`: Number of ranking criteria
- `has_bias_config`: Boolean indicating bias configuration
- `status`: Initial status of run

## Statistics Object

When filtering by `run_id`, the API automatically calculates statistics from all events for that run:

- **total_events**: Total number of events for this run
- **event_types**: Count of each event type
- **has_completion**: Boolean - did the run complete?
- **has_failure**: Boolean - did the run fail?
- **candidates_evaluated**: Number of candidates processed (from completion event)
- **scores_created**: Number of scores generated (from completion event)
- **total_duration_seconds**: Total execution time (from completion event)
- **score_statistics**: Score distribution statistics (from completion event)
- **error**: Error message (from failure event)
- **error_type**: Error type (from failure event)

## Example Requests

### Get all ranking events

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/audit/ranking/
```

### Get events for specific run with statistics

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/audit/ranking/?run_id=7e03b813-dd91-4ba2-900f-43dbd7f47696
```

### Get only failed runs

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/audit/ranking/?event_type=ranking.run.failed
```

### Get recent 50 events

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/audit/ranking/?limit=50
```

## Use Cases

### 1. Monitor Active Ranking Runs
Query for "ranking.run.started" events to see currently running or recently started ranking operations.

### 2. Debug Failed Runs
Filter by `event_type=ranking.run.failed` to investigate errors, then use the `run_id` to get full event history.

### 3. Performance Analysis
Use `run_id` filter to get complete statistics for a run, including duration metrics and score distributions.

### 4. Audit Trail
Review all ranking operations for compliance and transparency requirements.

### 5. Quality Monitoring
Track score statistics across multiple runs to identify potential issues with ranking algorithm or data quality.

## Error Responses

### 403 Forbidden
User has no associated organization:
```json
{
  "detail": "User has no organization"
}
```

### 401 Unauthorized
Invalid or missing authentication token:
```json
{
  "detail": "Authentication credentials were not provided."
}
```

## Implementation Notes

- Events are automatically created by the `RankingService` during run execution
- Events are ordered by creation time (newest first)
- All times are in UTC
- The API respects organization boundaries - users only see events from their organization
- Statistics are only calculated when filtering by `run_id` for performance reasons
- Maximum limit of 1000 results prevents excessive data transfer

## Related Endpoints

- `/api/audit/logs/` - General audit log query (includes ranking events)
- `/api/audit/events/` - CV access events (separate from ranking events)
- `/api/ranking/create/` - Create and execute ranking runs
- `/api/ranking/<run_id>/results/` - Get final ranking results
