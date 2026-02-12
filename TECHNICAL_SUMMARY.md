# NYOS APR — Technical Summary

**Version:** v0.9-beta | **Date:** February 2026 | **Team:** NYOS

---

## 1. Overview of Improvements Since MVP

The MVP delivered a basic dashboard with a single chat endpoint. Since then, the platform has been rebuilt into a **production-grade pharmaceutical quality intelligence system** with six major improvements:

| Area | MVP | Current (v0.9) |
|------|-----|----------------|
| **Analytics** | Single dashboard page | 5 analytics modules (drift detection, anomaly detection, period comparison, supplier performance, equipment analysis) |
| **AI** | Basic single-prompt chat | Multi-conversation threads, streaming summaries, context-aware analysis with full database access |
| **Reports** | None | 3-tier hierarchical system (FileReport → MonthlyReport → APR) with PDF export |
| **Data** | Manual CSV only | Built-in synthetic data generator (9 categories, configurable scenarios) + CSV import with auto-analysis |
| **Backend** | 5 endpoints | 70+ REST endpoints across 5 routers |
| **Deployment** | Local only | Dockerized, deployed on Render with CI/CD pipeline |

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│   React 18 + Vite + Tailwind CSS + Recharts                │
│   [Dashboard] [Analytics] [Trends] [Chat] [Import] [Gen]   │
└───────────────────────┬─────────────────────────────────────┘
                        │  REST API (same-origin in production)
┌───────────────────────▼─────────────────────────────────────┐
│                     FastAPI Backend                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │ /chat    │ │ /data    │ │/analytics│ │ /reports      │  │
│  │ /generate│ │ /health  │ │          │ │ (3-tier APR)  │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └───────┬───────┘  │
│       │            │            │               │           │
│  ┌────▼────────────▼────────────▼───────────────▼────────┐  │
│  │                  Services Layer                        │  │
│  │  gemini_service  │  report_service  │  pdf_service    │  │
│  │  data_generation_service                              │  │
│  └───────────┬──────────────────┬────────────────────────┘  │
│              │                  │                            │
│  ┌───────────▼──────┐  ┌───────▼────────┐                  │
│  │  Google Gemini   │  │    SQLite      │                  │
│  │  (AI/LLM API)    │  │  (16 tables)   │                  │
│  └──────────────────┘  └────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                        │
              Docker Multi-Stage Build
              (Node build → Python runtime)
                        │
                  Render (Free Tier)
```

**Key architectural decisions:**
- **Single-container deployment**: Frontend is built at Docker build time and served by FastAPI as static files. This eliminates CORS issues and simplifies deployment.
- **SQLite**: Zero-config database suitable for the data volumes of a single-plant APR. Data persists within the container and can be pre-loaded.
- **Google Gemini API**: Direct API integration (free tier: 60 req/min) for all AI features — chat, summaries, and report generation.

---

## 3. Data & Model Improvements

### Synthetic Data Engine
We built a configurable **PharmaceuticalDataGenerator** that produces 9 interconnected datasets following real pharmaceutical manufacturing patterns:

- **Manufacturing Batches**: CPPs (compression force, hardness, weight, thickness), equipment assignment, yield tracking
- **QC Results**: CQAs per ICH specs (assay 95-105%, dissolution >80%), microbial data
- **Complaints, CAPAs, Equipment, Environmental, Stability, Raw Materials, Batch Release**

### Embedded Scenarios (for AI validation)
The generator deterministically embeds 7 hidden quality events:

| Period | Scenario | Signal |
|--------|----------|--------|
| Mar-May 2020 | COVID-19 disruption | Reduced output, lower yields |
| Sep-Nov 2021 | Press-A degradation | Gradual hardness drift |
| Jun 2022 | MCC excipient issue | Dissolution drop, complaint spike |
| Q2 2023 | Lab method transition | Assay bias shift (+1.5%) |
| Jul-Aug 2024 | Seasonal temperature effect | Environmental excursions |
| Aug 2025 | Press-B drift | Hardness increase, OOS results |
| Nov-Dec 2025 | New API supplier | Yield adjustment, CAPA increase |

### AI Integration
- **Context building**: Every AI call receives a dynamically assembled context from the database (recent batches, QC results, open complaints, CAPAs, statistics)
- **Models used**: `gemini-2.5-flash-lite` for chat and streaming, `gemini-2.5-flash` for full report generation
- **Quality Score**: Weighted composite (QC pass rate 40%, yield 25%, complaints 20%, equipment 15%) displayed as a 0-100 gauge

---

## 4. Deployment Setup

| Component | Technology | Notes |
|-----------|-----------|-------|
| **Container** | Docker (multi-stage) | Stage 1: Node 18 builds React; Stage 2: Python 3.11 runs FastAPI + serves static |
| **Hosting** | Render (free tier) | Auto-deploys from GitHub on push |
| **CI/CD** | GitHub → Render | Also includes `cloudbuild.yaml` for Google Cloud Run |
| **Database** | SQLite (in-container) | Pre-loaded via data generation + import |
| **AI API** | Google Gemini | Free tier, API key via environment variable |

**Live URL:** Deployed on Render (public, no authentication required)

---

## 5. Results & Feedback

### Qualitative Results
- The AI assistant correctly identifies all 7 embedded scenarios when asked targeted questions
- Report generation produces regulatory-style APR documents with real statistics (no placeholder text)
- Quality Score accurately reflects plant status — drops during simulated events, recovers after resolution

### Performance Metrics
- **Dashboard load**: <2s (API + render)
- **AI chat response**: 3-8s depending on context size
- **Full APR generation**: 15-30s (multiple Gemini calls)
- **Data generation**: 5-10s for 1 month (620 batches + all related data)

---

## 6. Known Limitations & Next Steps

### Current Limitations
- **SQLite**: Not suitable for multi-user concurrent writes; adequate for single-plant demo
- **Memory**: Free tier hosting (512MB) limits data generation to ~1 month at a time
- **No authentication**: The deployed app is fully public with no user management
- **Ephemeral storage**: SQLite data is lost when the container restarts on Render free tier

### Next Steps
- **Persistent database**: Migrate to Cloud SQL or Supabase for production use
- **User authentication**: Add Google OAuth for multi-tenant access
- **Real-time monitoring**: WebSocket integration for live production data feeds
- **Enhanced AI**: Fine-tune prompts for specific regulatory frameworks (FDA, EMA)
- **Export formats**: Add Word/Excel export alongside PDF
- **Multi-product support**: Extend beyond Paracetamol to the full product portfolio
