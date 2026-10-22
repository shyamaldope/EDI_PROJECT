# EDI_PROJECT: Autonomous Agentic Citizen Welfare & Policy Intelligence Platform

This repository contains the complete implementation of the **Autonomous Agentic Citizen Welfare & Policy Intelligence Platform** (`welfare-navigator-platform`).

## Repository Organization

```
EDI_PROJECT/
├── README.md                          # Repository overview and entry point
├── .gitignore                         # Project-wide ignore definitions
└── welfare-navigator-platform/        # Core platform monorepo
    ├── backend/                       # FastAPI asynchronous backend service
    │   ├── database/                  # SQLAlchemy models, SQLite/PostgreSQL connectors & seed scripts
    │   ├── modules/                   # 6 Core architectural modules (Rule Engine, Document Auditor,
    │   │                              # AST Parser, RPA Co-Pilot, Policy Twin, SLA Grievance)
    │   ├── tests/                     # Automated pytest suite (23 integration and unit tests)
    │   ├── config.py                  # Environment settings & fallbacks
    │   ├── main.py                    # API routes, WebSocket streaming, and background task handlers
    │   └── requirements.txt           # Python dependencies
    ├── frontend/                      # Vite + React 18 + TailwindCSS citizen and admin web portal
    │   ├── src/                       # Components, pages, routing, and API clients
    │   ├── package.json               # Node.js dependencies
    │   └── tailwind.config.js         # Design system configuration
    ├── mock_gov_portals/              # Ethical self-hosted clones of MahaDBT and PM-KISAN portals
    │   ├── mahadbt_clone/             # MahaDBT mock portal HTML/CSS
    │   ├── pmkisan_clone/             # PM-KISAN mock portal HTML/CSS
    │   └── server.py                  # Standalone FastAPI portal server (port 8001)
    ├── sample_artifacts/              # Pre-generated synthetic test documents & GR PDFs
    ├── docs/                          # Comprehensive architectural, security, and usage documentation
    │   ├── ARCHITECTURE.md            # Neuro-symbolic boundary & data-flow specification
    │   ├── API_SPECIFICATION.md       # REST and WebSocket endpoint definitions
    │   ├── SECURITY_AND_PRIVACY.md    # DPDP Act 2023 alignment & PII scrubbing protocols
    │   ├── DECISION_LOG.md            # Architectural and engineering design decisions
    │   ├── ROADMAP_AND_STATUS.md      # Implementation milestone tracking
    │   └── USER_GUIDE_AND_FEATURE_AUDIT.md # Role-by-role user guide & comprehensive feature audit
    ├── docker-compose.yml             # Full-stack containerization specification
    ├── Makefile                       # Developer automation targets
    └── .env.example                   # Environment variable template
```

## Quick Start & Verification

1. **Backend & Mock Portals:**
   ```bash
   cd welfare-navigator-platform
   pip install -r backend/requirements.txt
   python backend/database/seed.py
   python backend/main.py               # Starts on port 8000
   python mock_gov_portals/server.py   # Starts on port 8001
   ```

2. **Frontend Portal:**
   ```bash
   cd welfare-navigator-platform/frontend
   npm install
   npm run dev                         # Starts on port 5173
   ```

3. **Automated Test Suite:**
   ```bash
   cd welfare-navigator-platform
   pytest backend/tests/ -v
   ```

Refer to [`welfare-navigator-platform/README.md`](welfare-navigator-platform/README.md) and [`welfare-navigator-platform/docs/USER_GUIDE_AND_FEATURE_AUDIT.md`](welfare-navigator-platform/docs/USER_GUIDE_AND_FEATURE_AUDIT.md) for full architectural details and audit records.
