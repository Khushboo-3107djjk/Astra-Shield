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

### Frontend
- React / Vue.js
- Leaflet / Mapbox (mapping)
- Chart.js / Plotly (visualization)
- Tailwind CSS / Material UI

### Backend
- FastAPI (Python)
- PostgreSQL / MongoDB
- GDAL (geospatial processing)

### ML/AI
- PyTorch / TensorFlow
- OpenCV (image processing)
- YOLO / U-Net (object detection & segmentation)
- Scikit-learn (evaluation)

### DevOps
- Docker
- Docker Compose
- GitHub

---

## 🚀 Getting Started

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
