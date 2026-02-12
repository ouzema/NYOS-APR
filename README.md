# NYOS APR - Pharmaceutical Quality Intelligence Platform

<p align="center">
  <img src="frontend/public/logo.svg" alt="NYOS Logo" width="280"/>
</p>

<p align="center">
  <strong>AI-Powered Annual Product Review & Manufacturing Analytics</strong>
</p>

<p align="center">
  <a href="#features">Features</a> &bull;
  <a href="#architecture">Architecture</a> &bull;
  <a href="#getting-started">Getting Started</a> &bull;
  <a href="#deployment">Deployment</a> &bull;
  <a href="#demo">Demo</a>
</p>

---

## Overview

NYOS APR is a full-stack pharmaceutical quality intelligence platform designed for **Annual Product Review (APR)** analysis. It combines interactive analytics dashboards, a synthetic data generation engine, and an AI assistant powered by **Google Gemini** to help pharmaceutical quality teams monitor manufacturing performance, detect process drifts, investigate anomalies, and generate regulatory-ready reports.

The platform covers the complete APR lifecycle: from raw data ingestion through statistical analysis to AI-generated annual reviews with PDF export.

---

## Features

### Analytics Dashboard
- **Real-time KPI monitoring** with trend indicators (batch volumes, yield, complaints, CAPAs, equipment status)
- **Quality Score** (0-100) calculated from QC pass rate, yield, complaints, and equipment calibration compliance
- **Interactive charts** for production trends, yield distribution, complaint categories, and CAPA status
- **Drill-down views** from high-level KPIs to individual batch details

### Advanced Analytics
- **Drift Detection** - Identify gradual parameter shifts with configurable time windows
- **Anomaly Detection** - Flag out-of-specification conditions and unusual patterns
- **Period Comparison** - Compare any two time periods side by side
- **Supplier Performance** - Track material quality, rejection rates, and delivery metrics
- **Equipment Analysis** - Monitor calibration compliance and performance by machine

### AI Assistant (Google Gemini)
- **Natural language querying** - Ask questions about your data in plain English
- **Context-aware responses** - AI has access to the full database for comprehensive analysis
- **Streaming executive summaries** - Real-time generation via Server-Sent Events
- **Multi-conversation support** - Maintain multiple analysis threads with persistent history

### Hierarchical Report Generation
A 3-tier report system designed for incremental, auditable report building:

```
CSV Upload  -->  FileReport (Level 1)  -->  MonthlyReport (Level 2)  -->  APR (Level 3)  -->  PDF Export
                 Per-file AI analysis       Monthly aggregation           Annual synthesis       Regulatory-ready
```

- **Level 1 - FileReport**: Automatically generated when a CSV is uploaded. Includes AI-powered summary, key metrics extraction, and anomaly detection.
- **Level 2 - MonthlyReport**: Aggregates all FileReports for a given month into production, quality, and compliance analyses.
- **Level 3 - APR Report**: Synthesizes monthly reports into a comprehensive Annual Product Review with executive summary, trend analysis, conclusions, and recommendations.
- **PDF Export**: Professional, branded PDF documents suitable for regulatory submission.

### Synthetic Data Generation
A built-in data generation engine that creates realistic pharmaceutical manufacturing data:

- **9 data categories**: Manufacturing batches, QC results, complaints, CAPAs, equipment calibration, environmental monitoring, stability studies, raw materials, and batch release records
- **Configurable parameters**: Batches per day, date ranges, specific data types
- **Embedded scenarios**: Hidden quality events for testing AI detection capabilities:
  - 2020: COVID-19 production impact
  - 2021: Press-A equipment degradation (Sept-Nov)
  - 2022: Excipient supplier issue - MCC (June)
  - 2023: Analytical method transition (Q2)
  - 2024: Seasonal temperature effect (Jul-Aug)
  - 2025: Press-B drift + New API supplier (Nov)
- **Download as ZIP** with month, year, or custom date range granularity

### Parameter Trend Analysis
- Track 5 key parameters: Hardness, Yield, Compression Force, Weight, Thickness
- Configurable time ranges (7 days to 2 years)
- Specification limit bands and target reference lines
- Statistical summary (mean, min, max, std dev)

### Data Import
- Drag-and-drop CSV upload interface
- Support for all 9 data types with automatic type detection
- Import history tracking with record counts
- Automatic FileReport generation upon upload

---

## Architecture

### Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18, Vite, Tailwind CSS | Single-page application with responsive UI |
| **Charts** | Recharts | Interactive data visualizations |
| **Icons** | Lucide React | Consistent iconography |
| **Backend** | FastAPI (Python) | Async REST API with auto-generated docs |
| **ORM** | SQLAlchemy 2.0 | Database abstraction and query building |
| **Database** | SQLite | Lightweight, zero-config storage |
| **AI** | Google Generative AI (Gemini) | Chat, analysis, and report generation |
| **PDF** | ReportLab | Professional PDF report export |
| **Data Gen** | Pandas, Faker | Synthetic pharmaceutical dataset generation |

### Project Structure

```
nyos-apr/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point + static file serving
│   │   ├── config.py                # Environment configuration
│   │   ├── db.py                    # Database engine and session
│   │   ├── models.py                # 16 SQLAlchemy models
│   │   ├── schemas.py               # Pydantic request/response schemas
│   │   ├── routers/
│   │   │   ├── chat.py              # Conversations, chat, reports
│   │   │   ├── data.py              # Data retrieval, upload, dashboard
│   │   │   ├── analytics.py         # Advanced analytics endpoints
│   │   │   ├── reports.py           # Hierarchical report generation
│   │   │   └── generation.py        # Synthetic data generation
│   │   ├── services/
│   │   │   ├── gemini_service.py    # Gemini AI integration
│   │   │   ├── report_service.py    # 3-tier report generation logic
│   │   │   ├── data_generation_service.py  # Pharmaceutical data generator
│   │   │   └── pdf_service.py       # PDF report rendering
│   │   └── assets/
│   │       └── logo.svg
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── App.jsx                  # Main app with tab navigation
│   │   ├── api.js                   # API client (70+ endpoints)
│   │   └── components/
│   │       ├── Dashboard.jsx        # KPI dashboard with quality score
│   │       ├── Analytics.jsx        # Advanced analytics views
│   │       ├── Trends.jsx           # Parameter trend analysis
│   │       ├── Chat.jsx             # AI assistant interface
│   │       ├── DataUpload.jsx       # CSV import with drag-and-drop
│   │       └── Backoffice.jsx       # Data generation backoffice
│   ├── public/
│   │   ├── logo.svg
│   │   └── logo-icon.svg
│   └── package.json
├── generate_all_data.py             # Master data generation script
├── import_all_data.py               # Bulk data import script
├── Dockerfile                       # Multi-stage build (frontend + backend)
├── cloudbuild.yaml                  # Google Cloud Build config
└── README.md
```

### Database Schema

The application uses 16 tables covering the full pharmaceutical manufacturing lifecycle:

**Manufacturing & Quality**
- `Batch` - Production batch records with Critical Process Parameters
- `QCResult` - Lab results with Critical Quality Attributes (assay, dissolution, impurities)
- `BatchRelease` - QP release decisions and disposition

**Compliance & Governance**
- `Complaint` - Customer complaints with investigation tracking
- `CAPA` - Corrective/Preventive Actions with root cause analysis

**Infrastructure**
- `Equipment` - Calibration records and maintenance logs
- `Environmental` - Cleanroom monitoring (particles, temperature, humidity)
- `RawMaterial` - Supplier receipts and material disposition
- `Stability` - ICH stability studies (long-term, accelerated, intermediate)

**Application**
- `Conversation` / `ChatMessage` - AI chat threads
- `Report` - Saved report history
- `UploadedFile` / `FileReport` / `MonthlyReport` / `APRReport` - Hierarchical report system

---

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 18+ and npm
- A [Google Gemini API Key](https://aistudio.google.com/apikey) (free tier: 60 requests/minute)

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/NYOS-APR.git
cd NYOS-APR
```

### 2. Backend Setup

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate    # macOS/Linux
# .venv\Scripts\activate     # Windows

# Install dependencies
cd backend
pip install -r requirements.txt

# Create environment file
cat > .env << EOF
GOOGLE_API_KEY=your-gemini-api-key-here
DATABASE_URL=sqlite:///./nyos.db
EOF

# Start the backend server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API is now running at `http://localhost:8000`. Interactive docs available at `http://localhost:8000/docs`.

### 3. Generate and Import Data

Open a **new terminal** (keep the backend running):

```bash
# Generate synthetic pharmaceutical datasets (2020-2025)
python3 generate_all_data.py

# Import generated data into the database
python3 import_all_data.py
```

This creates ~6 years of realistic manufacturing data across 9 categories in the `apr_data/` directory and populates the database.

### 4. Frontend Setup

Open another **new terminal**:

```bash
cd frontend
npm install
npm run dev
```

### 5. Open the Application

Navigate to **[http://localhost:5173](http://localhost:5173)** in your browser.

---

## Deployment

### Docker (Recommended)

The project includes a multi-stage Dockerfile that builds the frontend and serves it alongside the backend from a single container.

```bash
# Build the image
docker build -t nyos-apr .

# Run the container
docker run -p 8080:8080 \
  -e GOOGLE_API_KEY=your-key-here \
  -e DATABASE_URL=sqlite:///./nyos.db \
  nyos-apr
```

Access the app at `http://localhost:8080`.

### Render (Free Hosting)

1. Push this repository to GitHub
2. Sign up at [render.com](https://render.com) and connect your GitHub account
3. Create a **New Web Service** and select this repository
4. Set **Runtime** to **Docker** and **Instance Type** to **Free**
5. Add environment variables: `GOOGLE_API_KEY` and `DATABASE_URL=sqlite:///./nyos.db`
6. Deploy - you'll get a public URL like `https://nyos-apr.onrender.com`

### Google Cloud Run

A `cloudbuild.yaml` is included for CI/CD with Google Cloud Build and Cloud Run.

```bash
gcloud builds submit --config=cloudbuild.yaml
```

---

## API Reference

The backend exposes 70+ REST endpoints organized into 5 routers:

| Router | Prefix | Key Endpoints |
|--------|--------|--------------|
| **Chat** | `/chat` | Conversations, AI chat, streaming summaries, report generation |
| **Data** | `/data` | Dashboard, batches, QC, complaints, CAPAs, CSV upload |
| **Analytics** | `/analytics` | Overview, drift detection, anomalies, supplier/equipment analysis |
| **Reports** | `/reports` | FileReports, MonthlyReports, APR generation, PDF export |
| **Generation** | `/generate` | Data type listing, month/year/custom data generation, ZIP download |

Full interactive API documentation is available at `/docs` when the backend is running.

---

## Dataset Overview

The synthetic data engine generates a complete pharmaceutical dataset for **Paracetamol 500mg Tablets** covering 2020-2025:

| Category | Description | Key Fields |
|----------|-------------|------------|
| **Manufacturing** | Batch production records | Yield, hardness, compression force, equipment IDs |
| **QC Results** | Lab testing data | Assay (95-105%), dissolution (>80%), impurities |
| **Complaints** | Customer complaints | Category, severity, investigation outcome |
| **CAPAs** | Corrective/Preventive Actions | Type, risk score, root cause, closure timeline |
| **Equipment** | Calibration records | As-found/as-left values, pass/fail, tolerance |
| **Environmental** | Cleanroom monitoring | Particle counts, temperature, humidity |
| **Stability** | ICH stability studies | Long-term, accelerated, intermediate conditions |
| **Raw Materials** | Supplier receipts | Test status, disposition, COA tracking |
| **Batch Release** | QP release decisions | Days-to-release, deviations, market destination |

---

## Demo

https://youtu.be/1mw6pO0CnSs

---

## License

This project was built for the Google Cloud Hackathon.
