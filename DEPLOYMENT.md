# Market Radar - SaaS Transformation Guide

## 🚀 Deployment Checklist

### Phase 1-4 Complete ✅

#### 1. Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your_key_here"
export FLASK_SECRET_KEY="your_secure_random_key_here"
```

#### 2. Database Migration
```bash
# Initialize database with new schema
python -c "from sources.database import init_db; init_db()"

# Run full pipeline to populate data
python run_pipeline.py
```

#### 3. Production Deployment

**Replace Development Server:**
```bash
# Install production WSGI server
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api.server:app
```

**Security Hardening:**
1. Generate secure SECRET_KEY and store in environment
2. Enable HTTPS (nginx + certbot recommended)
3. Set up CORS properly for your domain
4. Add rate limiting (Flask-Limiter)
5. Enable SQL injection protection (parameterized queries already in place)

**Environment Variables for Production:**
```
FLASK_SECRET_KEY=<strong-random-key>
OPENAI_API_KEY=<your-key>
DATABASE_PATH=/opt/market-radar/data/market_radar.db
FLASK_ENV=production
```

#### 4. Monitoring & Maintenance

**Scheduled Tasks (cron):**
```cron
# Run pipeline every 6 hours for Free users
0 */6 * * * /path/to/python /path/to/market-radar/run_pipeline.py

# Cleanup old data weekly
0 0 * * 0 /path/to/python /path/to/market-radar/scripts/cleanup.py
```

**Database Backups:**
```bash
# Daily backup
0 2 * * * cp /opt/market-radar/data/market_radar.db /backups/market_radar_$(date +\%Y\%m\%d).db
```

---

## 📋 Next Phases (Roadmap)

### Phase 5: Background Tasks & Queue (celery/redis)
- [ ] Async pipeline execution
- [ ] Email notifications for Pro users
- [ ] Scheduled deep scans
- [ ] CSV export generation

### Phase 6: Payment Integration
- [ ] Stripe/Mercado Pago integration
- [ ] Subscription management
- [ ] Credit system enforcement
- [ ] Upgrade/downgrade flows

### Phase 7: Advanced Features
- [ ] Historical price tracking
- [ ] Custom alert rules
- [ ] API access for Pro users
- [ ] Webhooks for automation

### Phase 8: Scale & Optimization
- [ ] PostgreSQL migration
- [ ] Redis caching layer
- [ ] CDN for static assets
- [ ] Load balancing

---

## 🎯 SaaS Metrics to Track

1. **Acquisition**
   - Landing page conversion rate
   - Signup to activation rate
   - Traffic sources

2. **Activation**  
   - First opportunity viewed
   - First saved opportunity
   - Dashboard engagement

3. **Revenue**
   - Free to Pro conversion rate
   - Monthly Recurring Revenue (MRR)
   - Average Revenue Per User (ARPU)

4. **Retention**
   - Daily/Weekly/Monthly Active Users
   - Churn rate
   - Feature usage patterns

5. **Referral**
   - Organic signups
   - User-generated content

---

## 🔧 Quick Commands

```bash
# Development
python api/server.py

# Production
gunicorn -w 4 api.server:app

# Run pipeline manually
python run_pipeline.py

# Create admin user
python -c "from sources.database import create_user; create_user('admin@example.com', 'password', 'Admin', 'admin')"

# Check database
sqlite3 data/market_radar.db "SELECT COUNT(*) FROM opportunities;"
```

---

## 📁 Project Structure

```
market-radar/
├── api/
│   ├── server.py         # Flask application (with auth)
│   └── auth.py           # Authentication blueprint
├── sources/
│   ├── database.py       # SQLite ORM (Phase 1-2)
│   ├── ai_processor.py   # AI clustering
│   ├── intent_signals.py # Signal gathering
│   └── mercado_livre.py  # Scraper with DB persistence
├── scoring/
│   └── ranker.py         # Opportunity ranking (with DB)
├── web/
│   ├── landing.html      # Public marketing page (Phase 4)
│   ├── login.html        # Auth page (Phase 2)
│   ├── index.html        # Dashboard (protected)
│   ├── app.js            # Dashboard logic (with auth check)
│   └── style.css         # Styling
├── data/
│   └── market_radar.db   # SQLite database
└── requirements.txt      # Dependencies
```

---

## 🎉 Completed Transformations

✅ **Phase 1**: Database persistence (clusters + opportunities)  
✅ **Phase 2**: User authentication & multi-tenancy  
✅ **Phase 3**: Enhanced UX (modals, save, toast)  
✅ **Phase 4**: Landing page & pricing  

**Next:** Background tasks, payment integration, and scale.
