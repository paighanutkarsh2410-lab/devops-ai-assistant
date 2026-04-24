# Learning Agent

The Learning Agent makes the SentryAI system smarter over time by learning from every resolved incident.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Learning Agent                           │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Knowledge   │  │   Pattern    │  │  Recommendation  │  │
│  │     Base      │  │  Recognizer  │  │     Engine       │  │
│  │  (Qdrant DB)  │  │  (Clusters)  │  │   (Rankings)     │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
│         │                 │                     │            │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌────────┴─────────┐  │
│  │  Embeddings   │  │ Correlation  │  │   Feedback Loop  │  │
│  │ (MiniLM-L6)   │  │   Matrix     │  │  (Auto-tuning)   │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         ↕                  ↕                    ↕
    ┌─────────┐      ┌───────────┐       ┌───────────┐
    │Diagnostic│      │ Monitor   │       │Remediation│
    │  Agent   │      │  Agent    │       │   Agent   │
    └─────────┘      └───────────┘       └───────────┘
```

## How It Works

### Learning Pipeline

1. **Incident Resolved** → Learning Agent is triggered
2. **Fetch Data** → Gets incident details, diagnostic results, remediation actions
3. **Extract Pattern** → Classifies the incident (memory_leak, cpu_spike, etc.)
4. **Generate Embedding** → Creates a 384-dim vector from incident text
5. **Store in Qdrant** → Saves embedding + metadata in vector database
6. **Update Statistics** → Updates action success rates and pattern frequencies

### Integration with Other Agents

**Diagnostic Agent:**
- Before calling Claude API, checks the vector KB for a learned diagnosis
- If similarity > 85% and the past incident was successful → uses learned diagnosis
- Saves LLM API costs and reduces diagnosis time

**Remediation Agent:**
- Before selecting an action, checks the Recommendation Engine
- Uses the top recommended action if confidence >= 60%
- Records outcome back to the Feedback Loop after execution

**Monitor Agent:**
- Learns normal baselines per service+metric
- Applies learned threshold adjustments to reduce false positives
- Updates baselines every 10 monitoring cycles

## Components

### Knowledge Base (Qdrant)
- Vector database storing incident embeddings
- Cosine similarity search for finding similar past incidents
- Payload indexes on service_name, severity, success
- Free tier: 1GB storage, sufficient for thousands of incidents

### Embeddings
- Model: `all-MiniLM-L6-v2` (384 dimensions)
- Weighted combination of title (0.4), description (0.3), root_cause (0.2), service (0.1)
- Redis caching with 24h TTL to avoid recomputing
- Fallback to hash-based embeddings if model unavailable

### Pattern Recognition
- 9 pattern types: memory_leak, cpu_spike, api_timeout, disk_full, database_slow, deployment_issue, cache_issue, network_issue, process_stuck
- DBSCAN clustering on embeddings (with keyword fallback)
- Frequency tracking with trending detection (increasing/decreasing/stable)
- Pattern → Root Cause → Solution correlation matrix

### Feedback Loop
- Records every remediation outcome (success/failure)
- Adjusts anomaly detection thresholds based on false positive/negative rates
- Updates action preference scores (rewards success, penalizes failure)
- Learns normal resource baselines per service
- Persists state to disk for durability

### Recommendation Engine
- Ranks actions by: similarity * success_rate * speed_factor
- Confidence scoring (0-100)
- Explains recommendations with historical evidence
- Tracks recommendation acceptance rate

### Reports
- Weekly/monthly learning reports
- Insights generation (success rates, patterns, improvements)
- Knowledge gap identification
- Improvement recommendations

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /learning/data | Upsert learning data |
| GET | /learning/data | Get learning entries |
| POST | /learning/outcomes | Record action outcome |
| GET | /learning/outcomes/stats | Action success statistics |
| GET | /learning/patterns | Discovered patterns |
| POST | /learning/patterns | Upsert a pattern |
| GET | /learning/stats | Overall learning stats |
| POST | /learning/recommend | Get action recommendations |
| GET | /reports/learning/weekly | Weekly report |
| GET | /reports/learning/monthly | Monthly report |
| GET | /reports/learning/insights | Human-readable insights |

## Setup

### Qdrant Cloud (Recommended)

1. Create a free account at https://cloud.qdrant.io
2. Create a cluster (free tier: 1GB storage)
3. Copy the URL and API key
4. Add to `agents/.env`:

```env
QDRANT_URL=https://your-cluster.qdrant.io:6333
QDRANT_API_KEY=your-api-key-here
```

### Without Qdrant

The system works without Qdrant using in-memory storage. Set `QDRANT_URL=` (empty) to use this mode. Data won't persist across restarts.

### Install Dependencies

```bash
cd agents
pip install -r requirements.txt
```

New packages: `qdrant-client`, `sentence-transformers`, `scikit-learn`

## Configuration

See `agents/config/auto_tuning.yaml` for auto-tuning settings:

```yaml
auto_tuning:
  enabled: true
  learning_rate: 0.3
  min_data_points: 5
```

## Metrics Tracked

- **Knowledge Base hit rate**: % of diagnoses from memory vs LLM
- **Action success rates**: per action, per pattern
- **Detection accuracy**: precision, recall, F1 score
- **Average resolution time**: trending over time
- **Recommendation acceptance**: how often suggestions are followed

## Frontend

The Learning dashboard (`/learning`) shows:
- Stats cards: patterns discovered, success rate, outcomes, avg resolution time
- Weekly report with action performance breakdown
- Pattern discovery with trending indicators
- Human-readable insights and improvement suggestions
