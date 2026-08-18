# 🛰️ ASTRA-SHIELD
## AI-Powered Satellite Disaster Intelligence

**See. Understand. Respond.**

---

## 🚀 About the Project

ASTRA-SHIELD is an intelligent satellite disaster monitoring and response system developed for the Space Innovation Hackathon 2026 (Online Mode), organized by SVNIT Surat in association with SAC/ISRO.

### Theme
**Disaster Monitoring Using Satellite Images** — Develop AI-powered solutions for automatic analysis of satellite imagery to detect and monitor floods, cyclones, forest fires, landslides, earthquakes, and other natural disasters.

---

## 🎯 Key Features

- 🤖 **AI Disaster Detection** — Classify and segment disasters from satellite images
- 🗺️ **Geospatial Analysis** — Map affected areas and infrastructure impact
- ⚠️ **Risk Prioritization** — Identify critical zones for emergency response
- 📊 **Before/After Comparison** — Quantify disaster expansion and change
- 🚨 **Emergency Response System** — Generate actionable alerts and reports
- 🌍 **Multi-Disaster Support** — Flood | Wildfire | Cyclone | Landslide | Earthquake | Drought

---

## 📁 Project Structure

```
Astra-Shield/
│
├── frontend/                    # React/Vue web interface
│   ├── src/
│   │   ├── pages/              # Page components
│   │   ├── components/         # Reusable components
│   │   ├── services/           # API calls
│   │   └── utils/              # Helpers
│   └── public/
│
├── backend/                     # Python FastAPI backend
│   ├── app/
│   │   ├── api/                # API endpoints
│   │   ├── models/             # DB models
│   │   ├── services/           # Business logic
│   │   ├── schemas/            # Pydantic schemas
│   │   └── utils/              # Utilities
│   └── requirements.txt
│
├── ml/                          # 👩‍💻 Person 1 — ML/AI
│   ├── datasets/               # Training data
│   ├── preprocessing/          # Data preprocessing
│   ├── models/
│   │   ├── classifier/         # Disaster classification
│   │   └── segmentation/       # Disaster segmentation
│   ├── inference/              # Prediction pipeline
│   ├── evaluation/             # Metrics & evaluation
│   ├── outputs/                # Results & visualizations
│   └── notebooks/              # Experiments
│
├── demo/                        # 🛰️ Demo satellite data
│   ├── flood/
│   ├── wildfire/
│   └── landslide/
│
├── docs/                        # 📄 Documentation
│   ├── executive-summary.md
│   ├── technical-report.md
│   ├── architecture/
│   └── presentation/
│
├── .env.example
├── requirements.txt
├── docker-compose.yml
└── .gitignore
```

---

## 👥 Team Structure

### 👩‍💻 Person 1 — ML/AI Engineer
- AI model development & training
- Disaster detection & segmentation
- Inference pipeline
- **Deliverable**: `{disaster_type, confidence, severity, affected_area, mask}`

### 👨‍💻 Person 2 — Backend/Geospatial Developer
- Impact analysis & infrastructure mapping
- Risk assessment & zone prioritization
- Response recommendations
- **Deliverable**: Impact stats, risk zones, response actions

### 👩‍🎨 Person 3 — Frontend/UX Developer
- Web interface & dashboard
- Data visualization
- Interactive features
- **Deliverable**: 7-section web application

---

## 🌐 Website Structure (7 Sections)

1. **Mission Control** — Overview & launch analysis
2. **Satellite Analysis** — Image upload & disaster selection
3. **AI Detection** — Real-time AI processing
4. **Disaster Evolution** ⭐ — Before/After comparison slider
5. **Impact Intelligence** — Affected areas & infrastructure
6. **Risk & Emergency Priority** — Critical zones
7. **Response Center** — Emergency actions & alerts

---

## 🛠️ Tech Stack

### 🎨 Frontend
| Technology | Version | Purpose |
|---|---|---|
| **React** | 18.2.0 | UI framework |
| **React Router DOM** | 6.20.0 | Page navigation |
| **Tailwind CSS** | 3.4.0 | Styling |
| **Material UI** | 4.12.4 | UI components |
| **Leaflet** | 1.9.4 | Interactive mapping |
| **React Leaflet** | 4.2.1 | React wrapper for Leaflet |
| **Plotly.js** | 2.26.0 | Data visualization |
| **Recharts** | 2.10.3 | Chart components |
| **Axios** | 1.6.2 | HTTP client |

### 🔧 Backend
| Technology | Version | Purpose |
|---|---|---|
| **FastAPI** | 0.104.1 | Web framework |
| **Uvicorn** | 0.24.0 | ASGI server |
| **Pydantic** | 2.5.0 | Data validation |
| **SQLAlchemy** | 2.0.23 | ORM for databases |
| **Alembic** | 1.13.0 | Database migrations |
| **PostgreSQL** | 15 | Primary database |
| **MongoDB** | Latest | NoSQL option |
| **Python-dotenv** | 1.0.0 | Environment management |

### 🤖 ML/AI
| Technology | Version | Purpose |
|---|---|---|
| **PyTorch** | 2.1.1 | Deep learning framework |
| **TorchVision** | 0.16.1 | Computer vision models |
| **OpenCV** | 4.8.1.78 | Image processing |
| **NumPy** | 1.24.3 | Numerical computing |
| **Pandas** | 2.1.3 | Data processing |
| **Scikit-learn** | 1.3.2 | ML algorithms & evaluation |
| **Scikit-image** | 0.22.0 | Image processing utilities |
| **Pillow** | 10.1.0 | Image manipulation |

### 🌍 Geospatial & Remote Sensing
| Technology | Version | Purpose |
|---|---|---|
| **Rasterio** | 1.3.9 | Satellite image I/O |
| **GeoPandas** | 0.14.0 | Geospatial data processing |
| **Shapely** | 2.0.2 | Geometric objects |
| **Folium** | 0.14.0 | Map visualization |
| **GDAL** | Latest | Geospatial data library |
| **Imageio** | 2.33.1 | Image file I/O |

### 🚀 DevOps & Deployment
| Technology | Purpose |
|---|---|
| **Docker** | Container platform |
| **Docker Compose** | Multi-container orchestration |
| **Git/GitHub** | Version control |
| **Python 3.9+** | Backend runtime |
| **Node.js 16+** | Frontend runtime |

### 📊 Testing & Development
| Technology | Version | Purpose |
|---|---|---|
| **pytest** | 7.4.3 | Python testing framework |
| **Black** | 23.12.0 | Code formatter |
| **Flake8** | 6.1.0 | Linting |
| **@testing-library/react** | 14.1.2 | React component testing |

---

## � Tech Stack Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER (Port 3000)                  │
│  React 18.2 + Tailwind CSS + Material UI + Leaflet          │
│  ↓ Axios                                                      │
├─────────────────────────────────────────────────────────────┤
│                    API LAYER (Port 8000)                      │
│  FastAPI 0.104 + Uvicorn + Pydantic Validation              │
│  ├─ /api/analyze          → Route to ML Service              │
│  ├─ /api/impact           → Geospatial Analysis              │
│  ├─ /api/zones            → Risk Prioritization              │
│  └─ /api/emergency-alert  → Response Generation              │
│  ↓ SQLAlchemy ORM                                             │
├─────────────────────────────────────────────────────────────┤
│                    ML/AI LAYER                                │
│  PyTorch + OpenCV + Scikit-learn                             │
│  ├─ DisasterClassifier    → Classification (ResNet/EfficientNet)
│  └─ DisasterSegmenter     → Segmentation (U-Net/DeepLab)     │
│  ↓ Inference Pipeline                                         │
├─────────────────────────────────────────────────────────────┤
│                  GEOSPATIAL LAYER                             │
│  Rasterio + GeoPandas + Folium                               │
│  ├─ Infrastructure Impact → Building/Road/Hospital detection │
│  ├─ Risk Zones            → Zone A/B/C/D prioritization      │
│  └─ Map Visualization     → Leaflet/Folium rendering         │
│  ↓ SQLAlchemy                                                 │
├─────────────────────────────────────────────────────────────┤
│                    DATA LAYER (Port 5432)                     │
│  PostgreSQL 15 + Alembic Migrations                          │
│  (Optional: MongoDB for documents)                            │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow
```
Satellite Image
    ↓
[Frontend Upload] (Axios)
    ↓
[FastAPI /api/analyze]
    ↓
[PyTorch Inference]
  ├─ Classifier → disaster_type, confidence
  └─ Segmenter → mask, affected_area, severity
    ↓
[Geospatial Processing]
  ├─ Infrastructure Impact → buildings, roads, hospitals
  ├─ Risk Calculation → zones A/B/C/D
  └─ Response Generation → alerts, recommendations
    ↓
[PostgreSQL Storage]
    ↓
[Frontend Visualization]
  ├─ Before/After Slider
  ├─ Impact Map (Leaflet)
  ├─ Risk Zones (Folium)
  └─ Emergency Response Panel
```

---

### Prerequisites
- Python 3.9+
- Node.js 16+
- Docker & Docker Compose

### Installation

```bash
# Clone the repository
git clone https://github.com/Khushboo-3107djjk/Astra-Shield.git
cd Astra-Shield

# Backend setup
cd backend
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# ML setup
cd ../ml
pip install -r requirements.txt
```

### Running with Docker
```bash
docker-compose up --build
```

---

## 📊 Demo Scenarios

Pre-loaded demo data for testing:
- **Flood**: Satellite images before/after flooding
- **Wildfire**: Burn area detection
- **Landslide**: Terrain change detection

---

## 📄 Hackathon Submissions

- ✅ Executive Summary (1 page)
- ✅ Prototype (web application)
- ✅ Technical Report (≤10 pages)
- ✅ GitHub Repository (this project)

---

## 🏆 Evaluation Criteria

- **Innovation & Originality** — Unique disaster evolution feature
- **Feasibility & Scalability** — Multi-disaster architecture
- **Teamwork & Problem-solving** — Clear team roles & deliverables

---

## 📧 Contact

**Team Lead**: Khushboo
**Organization**: Sardar Vallabhbhai National Institute of Technology (SVNIT), Surat
**Event**: Space Innovation Hackathon 2026

---

## 📜 License

This project is developed for the Space Innovation Hackathon 2026. All rights reserved.

---

**🚀 Let's innovate for space! 🛰️**
