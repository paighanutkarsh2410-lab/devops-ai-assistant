# Troubleshooting

## Common Issues

### Backend won't start

**Port 8000 already in use:**
```bash
# Find process
netstat -ano | findstr ":8000"
# Kill it
taskkill /PID <pid> /F
```

**Database connection refused:**
```bash
# Check Docker is running
docker ps
# Restart PostgreSQL
docker compose restart postgres
```

### Frontend build errors

**Module not found:**
```bash
cd frontend
rm -rf node_modules .next
npm install
npm run dev
```

### Agent errors

**Claude API key invalid:**
- Check `agents/.env` has valid `ANTHROPIC_API_KEY`
- Test: `curl -H "x-api-key: $KEY" https://api.anthropic.com/v1/models`

**Qdrant connection failed:**
- Falls back to in-memory — not a blocker
- Check `QDRANT_URL` and `QDRANT_API_KEY` in `agents/.env`

**Slack notifications not sending:**
- Check `SLACK_BOT_TOKEN` has `chat:write` scope
- Ensure bot is invited to the channel
- Check `SlackNotifier.available` is `True`

### Database issues

**UUID serialization error:**
- Pydantic schemas need `@field_validator` for UUID→str conversion
- Check `schemas/approval.py` and `schemas/action_log.py` for examples

**"metadata" reserved name error:**
- SQLAlchemy reserves `metadata`. Use `extra_data = Column("metadata", JSON)` mapping

### Python version issues

**passlib/bcrypt error on Python 3.12:**
- We use `bcrypt` directly instead of `passlib`
- See `backend/src/utils/auth.py`

**pytest not found:**
- Use `py -3.12 -m pytest` (pytest installed on 3.12, not 3.10)

## Debug Procedures

### Check system health
```bash
curl http://localhost:8000/health
```

### Check agent logs
```bash
cd agents && python src/orchestrator.py  # Watch stdout
```

### Check database
```bash
docker exec -it devops-postgres psql -U devops_user -d devops_ai
\dt  -- list tables
SELECT COUNT(*) FROM incidents;
```

### Check Redis
```bash
docker exec -it devops-redis redis-cli
PING
KEYS cache:*
```
