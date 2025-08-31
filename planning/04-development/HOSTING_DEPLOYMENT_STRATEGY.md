# Hosting & Deployment Strategy - V2

## Executive Decision: Minimal Changes from V1

**Core Principle**: V1's infrastructure works. Don't fix what isn't broken.

## What We Keep from V1

### DigitalOcean App Platform ✅
- **Why keep**: Environment variables finally work, familiar platform
- **Cost**: ~$50-75/month
- **Components**:
  - PostgreSQL database (managed)
  - Valkey/Redis (managed)
  - Docker containers
  - App Platform orchestration

### Technology Stack ✅
- **PostgreSQL**: Primary database
- **Valkey/Redis**: Celery broker, caching
- **Docker**: Containerization
- **Celery**: Background tasks

## What Changes for V2

### 1. Environment Strategy (NEW)
```
Production (live customer data)
├── attackacrack-prod (existing)
└── Protected, manual deploys only

Staging (testing ground)
├── attackacrack-staging (NEW)
├── Separate database
├── Auto-deploy from main branch
└── Full integration testing

Local Development
├── Docker Compose
├── Local PostgreSQL + Redis
└── Hot reload everything
```

### 2. Deployment Pipeline

#### Local → Staging (Automatic)
```yaml
# GitHub Actions (.github/workflows/staging.yml)
on:
  push:
    branches: [main]

jobs:
  test:
    - Run pytest
    - Run Playwright tests
    - Check coverage >90%
  
  deploy-staging:
    - Build Docker image
    - Push to DigitalOcean registry
    - Deploy to attackacrack-staging
    - Run smoke tests
```

#### Staging → Production (Manual)
```bash
# Manual promotion when ready
doctl apps create-deployment $PROD_APP_ID \
  --image-tag $TESTED_TAG
```

### 3. Branch Strategy
```
main (staging auto-deploy)
├── feature/* (development)
├── fix/* (bug fixes)
└── hotfix/* (emergency production fixes)

production (protected, tags only)
└── v1.0.0, v1.0.1, etc.
```

## Infrastructure Setup

### DigitalOcean Resources
```yaml
# Production (existing, keep as-is)
attackacrack-prod:
  database: db-s-1vcpu-1gb ($15/mo)
  redis: db-valkey-1gb ($15/mo)
  web: basic-xs ($5/mo)
  worker: basic-xs ($5/mo)
  total: ~$40/month

# Staging (NEW, smaller)
attackacrack-staging:
  database: db-s-dev ($7/mo)
  redis: shared dev ($7/mo)
  web: basic-xxs ($4/mo)
  worker: basic-xxs ($4/mo)
  total: ~$22/month
```

### File Storage
**DigitalOcean Spaces** instead of Supabase
- $5/month for 250GB
- S3-compatible API
- CDN included
- Direct upload from browser

## Rejected Alternatives & Why

### ❌ Supabase
**Why mentioned in plan**: Real-time, auth, file storage
**Why skip for MVP**:
- Don't need real-time (polling works)
- FastAPI auth is simpler
- DigitalOcean Spaces cheaper
- One less service dependency

### ❌ Kubernetes
**Why considered**: "Modern" deployment
**Why skip**: 
- Overkill for single app
- App Platform simpler
- No DevOps team

### ❌ AWS/GCP/Azure
**Why considered**: More features
**Why skip**:
- DigitalOcean is working
- Simpler pricing
- Everything in one place

## Environment Variables Management

### Current Pain (V1)
- Manual entry through DigitalOcean UI
- Encrypted EV[] format hard to update
- No version control

### Solution (V2)
```bash
# .env.staging (git-ignored)
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
OPENPHONE_API_KEY=...

# Script to sync
./scripts/sync-env.sh staging

# Uses doctl to update all at once
doctl apps update $APP_ID --env-file .env.staging
```

## CI/CD Implementation

### GitHub Actions Workflow
```yaml
name: Deploy to Staging
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Tests
        run: |
          docker-compose up -d
          docker-compose exec web pytest
          docker-compose exec web playwright test
      
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build & Push
        run: |
          docker build -t registry.digitalocean.com/attack-a-crack/v2:$GITHUB_SHA .
          docker push registry.digitalocean.com/attack-a-crack/v2:$GITHUB_SHA
      
      - name: Deploy to Staging
        run: |
          doctl apps create-deployment $STAGING_APP_ID \
            --image-tag $GITHUB_SHA
```

## Monitoring & Observability

### Basic Monitoring (MVP)
- DigitalOcean built-in metrics
- Celery Flower for task monitoring
- PostgreSQL query performance
- Application logs in DigitalOcean

### Future Enhancements
- Sentry for error tracking
- DataDog for APM
- Custom health dashboard

## Backup Strategy

### Database Backups
- DigitalOcean automatic daily backups (7 day retention)
- Weekly manual backup to Spaces
- Before major deployments

### Code & Config
- Everything in Git
- Environment variables documented
- Infrastructure as code (app.yaml)

## Security Considerations

### Secrets Management
- All secrets in DigitalOcean encrypted variables
- Never in code or git
- Rotate quarterly
- Document in 1Password

### Network Security
- Database not publicly accessible
- Redis/Valkey internal only
- HTTPS only for web
- Rate limiting on API endpoints

## Cost Summary

### Total Monthly Cost
```
Production:        $40
Staging:          $22
Spaces (storage):  $5
Domain/SSL:        $0 (Cloudflare)
-------------------
Total:            $67/month
```

### Cost Optimization Tips
- Use dev-tier databases for staging
- Share Redis between staging services
- Clean old Docker images regularly
- Monitor Space usage

## Migration Plan from V1

### Phase 1: Setup Staging (Week 1)
1. Create staging app in DigitalOcean
2. Configure GitHub Actions
3. Test deployment pipeline
4. Verify all integrations work

### Phase 2: Parallel Running (Week 2-3)
1. Deploy V2 to staging
2. Keep V1 in production
3. Test thoroughly
4. Import production data to staging

### Phase 3: Cutover (Week 4)
1. Backup V1 completely
2. Put V1 in maintenance mode
3. Deploy V2 to production
4. Migrate data
5. Update DNS
6. Monitor closely

### Rollback Plan
- Keep V1 running for 30 days
- Database backup before cutover
- DNS switch for instant rollback
- Document rollback procedure

## Key Decisions

### DO:
✅ Keep DigitalOcean App Platform
✅ Add staging environment
✅ Automate staging deploys
✅ Manual production deploys
✅ Use DigitalOcean Spaces for files

### DON'T:
❌ Add Supabase (unnecessary complexity)
❌ Change database (PostgreSQL works)
❌ Switch cloud providers
❌ Over-engineer CI/CD
❌ Auto-deploy to production

## Success Criteria

### MVP Deployment Goals
- [ ] Staging auto-deploys from main branch
- [ ] Production requires manual approval
- [ ] Zero-downtime deployments
- [ ] Rollback possible in <5 minutes
- [ ] All tests pass before deploy

### Operational Goals
- [ ] <1 minute deploy time
- [ ] 99.9% uptime
- [ ] Automated backups working
- [ ] Monitoring alerts configured
- [ ] Team can deploy without DevOps

---

*Recommendation: Stick with what works. The only real change is adding a staging environment and automating deployments to it. Everything else stays the same because V1's infrastructure is solid.*