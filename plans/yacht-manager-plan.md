# PLAN.md — Yacht Management Software (SV Sausalito)
**Created:** 2026-03-18 | **Status:** Draft v1.0 | **Model:** Claude Sonnet 4.5

---

## Overview

A purpose-built yacht management web application for Eric Brown's 2022 Princess F50 motor yacht, homeported in Sausalito, CA. Inspired by Seahub (seahubsoftware.com), this app provides a centralized system for equipment tracking, maintenance scheduling, defect logging, parts inventory, checklists, document storage, and maintenance history. Built with Python/FastAPI + HTML/JS frontend on PostgreSQL, deployed Docker-first on Railway.

**Vessel:** 2022 Princess F50 | **Homeport:** Sausalito, CA | **Owner:** Eric Brown

---

## Execution Environment

| Criterion | Value | Decision |
|-----------|-------|----------|
| GPU required | No | MacBook Pro |
| Est. Docker build time | ~2 min | MacBook Pro |
| Docker image size | ~500MB | MacBook Pro |
| Codebase size | ~5K lines | MacBook Pro |
| RAM requirement | <4GB | MacBook Pro |
| GPU libraries | None | MacBook Pro |

**Selected environment:** MacBook Pro (Eric's)

---

## Deployment Architecture

- **Runtime:** Docker container on Railway
- **Base image:** `python:3.12-slim`
- **Services:** `web` (FastAPI), `db` (PostgreSQL 16), `redis` (optional cache/sessions)
- **Environment variables:**

| Variable | Description | Required |
|----------|-------------|----------|
| `PORT` | Railway-injected port | Yes |
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SECRET_KEY` | JWT signing key (32-char random) | Yes |
| `ADMIN_EMAIL` | Initial admin user email | Yes |
| `ADMIN_PASSWORD` | Initial admin password (hashed at startup) | Yes |
| `CORS_ORIGINS` | Allowed origins (comma-separated) | Yes |
| `UPLOAD_MAX_MB` | Max document upload size in MB (default: 50) | No |
| `REDIS_URL` | Redis URL for session cache (optional) | No |

- **Volumes/Storage:** PostgreSQL persistent volume on Railway; document uploads stored as base64 in DB or external S3 (Phase 2)
- **Railway template:** Standard Python + PostgreSQL template

---

## Architecture Decision Records

| ADR | Decision | Rationale | Alternatives Considered |
|-----|----------|-----------|------------------------|
| 1 | FastAPI + Jinja2 SSR | Simple, no SPA build step; works well on Railway; fast to build | React SPA (overkill for single-user), Django (heavier) |
| 2 | PostgreSQL (Railway managed) | Relational data fits well; Railway native support; rich querying for maintenance intervals | SQLite (not Railway-friendly, concurrent writes), MongoDB (schema flexibility not needed) |
| 3 | JWT auth (simple, stateless) | Single user + small crew; no OAuth complexity needed | Session cookies + Redis (added complexity), Basic Auth (insecure) |
| 4 | HTMX for interactivity | Progressive enhancement without full SPA; works with Jinja2 | Alpine.js, Vue (heavier), vanilla JS |
| 5 | Alembic migrations | Schema versioning from day one; Railway deployment safe | Raw SQL scripts (no versioning) |
| 6 | SQLAlchemy ORM | Type safety, migration support; FastAPI native integration | raw psycopg2 (more boilerplate), Tortoise ORM |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Railway DB connection limits on free tier | Medium | High | Use connection pooling (asyncpg/pgbouncer); upgrade to hobby tier |
| Document uploads filling Railway volume | Medium | Medium | Phase 1: store docs in DB as bytea; Phase 2: move to S3/Dropbox |
| Single-user auth → no role separation | Low | Low | Design auth layer to support roles from day one even if unused |
| Maintenance interval data inaccuracy | Medium | Medium | Pre-seed with factory specs; provide edit UI; note source |
| Migration ordering issues (extensions) | Low | High | CREATE EXTENSION in separate migration before table creation |
| .env secrets committed to git | Low | Critical | .gitignore checked pre-commit; use Railway env var UI, never .env in repo |
| Railway cold-start latency | Low | Low | Keep image small; use lightweight health check |

---

## Database Schema

### Tables

```sql
-- ─────────────────────────────────────────────
-- USERS
-- ─────────────────────────────────────────────
CREATE TABLE users (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(255) UNIQUE NOT NULL,
    name        VARCHAR(255) NOT NULL,
    role        VARCHAR(50) DEFAULT 'crew',  -- 'owner', 'captain', 'crew'
    password_hash TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    last_login  TIMESTAMPTZ
);

-- ─────────────────────────────────────────────
-- VESSEL (single row, Eric's F50)
-- ─────────────────────────────────────────────
CREATE TABLE vessel (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,   -- e.g. "Princess F50 — Sausalito"
    make        VARCHAR(100),            -- "Princess"
    model       VARCHAR(100),            -- "F50"
    year        INTEGER,                 -- 2022
    hull_id     VARCHAR(100),            -- HIN
    registration VARCHAR(100),
    homeport    VARCHAR(255),            -- "Sausalito, CA"
    flag        VARCHAR(10) DEFAULT 'US',
    notes       TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- EQUIPMENT CATEGORIES
-- ─────────────────────────────────────────────
CREATE TABLE equipment_categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,   -- "Propulsion", "Electrical", etc.
    icon        VARCHAR(50),             -- emoji or icon name
    sort_order  INTEGER DEFAULT 0
);

-- ─────────────────────────────────────────────
-- EQUIPMENT (the core asset register)
-- ─────────────────────────────────────────────
CREATE TABLE equipment (
    id              SERIAL PRIMARY KEY,
    vessel_id       INTEGER REFERENCES vessel(id),
    category_id     INTEGER REFERENCES equipment_categories(id),
    name            VARCHAR(255) NOT NULL,
    manufacturer    VARCHAR(100),
    model           VARCHAR(100),
    serial_number   VARCHAR(100),
    installation_date DATE,
    location        VARCHAR(255),        -- "Engine Room - Port", "Helm Station"
    status          VARCHAR(50) DEFAULT 'operational', -- operational|monitor|offline|retired
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- MAINTENANCE TASKS (scheduled recurring jobs)
-- ─────────────────────────────────────────────
CREATE TABLE maintenance_tasks (
    id              SERIAL PRIMARY KEY,
    equipment_id    INTEGER REFERENCES equipment(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    interval_type   VARCHAR(20) NOT NULL,  -- 'hours', 'days', 'months', 'years', 'miles'
    interval_value  INTEGER NOT NULL,       -- e.g. 250, 12, 1
    last_done_date  DATE,
    last_done_hours NUMERIC(10,1),         -- engine hours at last service
    next_due_date   DATE,
    next_due_hours  NUMERIC(10,1),
    priority        VARCHAR(20) DEFAULT 'normal', -- critical|high|normal|low
    assigned_vendor VARCHAR(255),
    estimated_cost  NUMERIC(10,2),
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- MAINTENANCE HISTORY (completed work log)
-- ─────────────────────────────────────────────
CREATE TABLE maintenance_history (
    id              SERIAL PRIMARY KEY,
    task_id         INTEGER REFERENCES maintenance_tasks(id) ON DELETE SET NULL,
    equipment_id    INTEGER REFERENCES equipment(id),
    vessel_id       INTEGER REFERENCES vessel(id),
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    performed_by    VARCHAR(255),          -- person or vendor name
    performed_date  DATE NOT NULL,
    engine_hours    NUMERIC(10,1),
    cost            NUMERIC(10,2),
    parts_used      TEXT,                  -- JSON array of part IDs or free text
    next_due_date   DATE,
    next_due_hours  NUMERIC(10,1),
    status          VARCHAR(50) DEFAULT 'completed', -- completed|partial|pending
    notes           TEXT,
    created_by      INTEGER REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- DEFECTS / SQUAWK LOG
-- ─────────────────────────────────────────────
CREATE TABLE defects (
    id              SERIAL PRIMARY KEY,
    vessel_id       INTEGER REFERENCES vessel(id),
    equipment_id    INTEGER REFERENCES equipment(id),
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    severity        VARCHAR(20) NOT NULL,   -- critical|high|medium|low
    status          VARCHAR(50) DEFAULT 'open', -- open|in_progress|resolved|deferred
    reported_by     VARCHAR(255),
    reported_date   DATE NOT NULL DEFAULT CURRENT_DATE,
    resolved_date   DATE,
    resolution_notes TEXT,
    assigned_vendor VARCHAR(255),
    estimated_cost  NUMERIC(10,2),
    actual_cost     NUMERIC(10,2),
    created_by      INTEGER REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- PARTS INVENTORY
-- ─────────────────────────────────────────────
CREATE TABLE parts (
    id              SERIAL PRIMARY KEY,
    vessel_id       INTEGER REFERENCES vessel(id),
    equipment_id    INTEGER REFERENCES equipment(id),
    part_number     VARCHAR(100),
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    manufacturer    VARCHAR(100),
    vendor          VARCHAR(255),           -- "West Marine", "Marea Marine", etc.
    vendor_url      TEXT,
    quantity_on_hand INTEGER DEFAULT 0,
    quantity_min    INTEGER DEFAULT 1,      -- reorder threshold
    unit_cost       NUMERIC(10,2),
    location        VARCHAR(255),           -- "Engine Room - Port Shelf", "Fore Cabin"
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- CHECKLISTS (templates)
-- ─────────────────────────────────────────────
CREATE TABLE checklists (
    id          SERIAL PRIMARY KEY,
    vessel_id   INTEGER REFERENCES vessel(id),
    name        VARCHAR(255) NOT NULL,
    category    VARCHAR(100),   -- 'departure', 'arrival', 'weekly', 'safety', 'passage'
    description TEXT,
    is_active   BOOLEAN DEFAULT TRUE,
    created_by  INTEGER REFERENCES users(id),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE checklist_items (
    id              SERIAL PRIMARY KEY,
    checklist_id    INTEGER REFERENCES checklists(id) ON DELETE CASCADE,
    sort_order      INTEGER DEFAULT 0,
    item_text       TEXT NOT NULL,
    notes           TEXT,
    equipment_id    INTEGER REFERENCES equipment(id)  -- optional link to equipment
);

-- ─────────────────────────────────────────────
-- CHECKLIST RUNS (completed instances)
-- ─────────────────────────────────────────────
CREATE TABLE checklist_runs (
    id              SERIAL PRIMARY KEY,
    checklist_id    INTEGER REFERENCES checklists(id),
    vessel_id       INTEGER REFERENCES vessel(id),
    run_date        DATE NOT NULL DEFAULT CURRENT_DATE,
    completed_by    VARCHAR(255),
    status          VARCHAR(50) DEFAULT 'in_progress', -- in_progress|complete
    notes           TEXT,
    created_by      INTEGER REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE checklist_run_items (
    id              SERIAL PRIMARY KEY,
    run_id          INTEGER REFERENCES checklist_runs(id) ON DELETE CASCADE,
    item_id         INTEGER REFERENCES checklist_items(id),
    checked         BOOLEAN DEFAULT FALSE,
    notes           TEXT,
    checked_at      TIMESTAMPTZ
);

-- ─────────────────────────────────────────────
-- DOCUMENTS
-- ─────────────────────────────────────────────
CREATE TABLE documents (
    id              SERIAL PRIMARY KEY,
    vessel_id       INTEGER REFERENCES vessel(id),
    equipment_id    INTEGER REFERENCES equipment(id),
    category        VARCHAR(100),   -- 'manual', 'certificate', 'insurance', 'invoice', 'photo'
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    filename        VARCHAR(255),
    mime_type       VARCHAR(100),
    file_data       BYTEA,          -- Phase 1: store in DB; Phase 2: S3 URL
    file_url        TEXT,           -- Phase 2: external storage URL
    expiry_date     DATE,           -- for certificates, insurance, etc.
    created_by      INTEGER REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- ENGINE HOURS LOG
-- ─────────────────────────────────────────────
CREATE TABLE engine_hours (
    id              SERIAL PRIMARY KEY,
    vessel_id       INTEGER REFERENCES vessel(id),
    equipment_id    INTEGER REFERENCES equipment(id),  -- port or stbd engine
    hours           NUMERIC(10,1) NOT NULL,
    recorded_date   DATE NOT NULL DEFAULT CURRENT_DATE,
    notes           TEXT,
    created_by      INTEGER REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- VENDORS
-- ─────────────────────────────────────────────
CREATE TABLE vendors (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    category    VARCHAR(100),    -- 'mechanic', 'parts', 'marina', 'chandlery'
    contact     VARCHAR(255),
    phone       VARCHAR(50),
    email       VARCHAR(255),
    website     TEXT,
    address     TEXT,
    notes       TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

---

## API Endpoints

### Authentication
```
POST   /api/auth/login              # {email, password} → JWT token
POST   /api/auth/logout             # Invalidate token
GET    /api/auth/me                 # Current user info
```

### Vessel
```
GET    /api/vessel                  # Get vessel details
PUT    /api/vessel                  # Update vessel details
GET    /api/vessel/dashboard        # Summary stats (open defects, due maintenance, etc.)
```

### Equipment
```
GET    /api/equipment               # List all equipment (filter: category, status)
POST   /api/equipment               # Create equipment item
GET    /api/equipment/{id}          # Get equipment detail + maintenance history
PUT    /api/equipment/{id}          # Update equipment
DELETE /api/equipment/{id}          # Soft delete (set status=retired)
GET    /api/equipment/categories    # List categories
```

### Maintenance Tasks
```
GET    /api/maintenance             # List tasks (filter: due_soon, overdue, equipment_id)
POST   /api/maintenance             # Create task
GET    /api/maintenance/{id}        # Task detail
PUT    /api/maintenance/{id}        # Update task
DELETE /api/maintenance/{id}        # Delete task
POST   /api/maintenance/{id}/complete  # Log completion → creates history record, updates next_due
GET    /api/maintenance/upcoming    # Due in next 30/60/90 days
GET    /api/maintenance/overdue     # Past due tasks
```

### Maintenance History
```
GET    /api/history                 # Full log (filter: equipment_id, date_range, vendor)
POST   /api/history                 # Add ad-hoc history entry
GET    /api/history/{id}            # Entry detail
PUT    /api/history/{id}            # Edit entry
DELETE /api/history/{id}            # Delete entry
```

### Defects
```
GET    /api/defects                 # List (filter: status, severity, equipment_id)
POST   /api/defects                 # Log new defect
GET    /api/defects/{id}            # Detail
PUT    /api/defects/{id}            # Update (including resolve)
DELETE /api/defects/{id}            # Delete
POST   /api/defects/{id}/resolve    # Mark resolved with notes
```

### Parts Inventory
```
GET    /api/parts                   # List (filter: equipment_id, low_stock)
POST   /api/parts                   # Add part
GET    /api/parts/{id}              # Detail
PUT    /api/parts/{id}              # Update
DELETE /api/parts/{id}              # Delete
POST   /api/parts/{id}/adjust       # Adjust quantity (+/-)
GET    /api/parts/low-stock         # Items below minimum quantity
```

### Checklists
```
GET    /api/checklists              # List templates
POST   /api/checklists              # Create template
GET    /api/checklists/{id}         # Template detail + items
PUT    /api/checklists/{id}         # Update template
POST   /api/checklists/{id}/run     # Start a new checklist run
GET    /api/checklists/runs         # List all runs
GET    /api/checklists/runs/{id}    # Run detail
PUT    /api/checklists/runs/{id}/items/{item_id}  # Check/uncheck item
POST   /api/checklists/runs/{id}/complete  # Complete run
```

### Documents
```
GET    /api/documents               # List (filter: category, equipment_id, expiring_soon)
POST   /api/documents               # Upload document (multipart)
GET    /api/documents/{id}          # Metadata
GET    /api/documents/{id}/download # Download file
PUT    /api/documents/{id}          # Update metadata
DELETE /api/documents/{id}          # Delete
GET    /api/documents/expiring      # Documents expiring in next 90 days
```

### Engine Hours
```
GET    /api/engine-hours            # List logs
POST   /api/engine-hours            # Record hours reading
GET    /api/engine-hours/current    # Latest reading per engine
```

### Vendors
```
GET    /api/vendors                 # List vendors
POST   /api/vendors                 # Create vendor
GET    /api/vendors/{id}            # Detail
PUT    /api/vendors/{id}            # Update
DELETE /api/vendors/{id}            # Delete
```

### System
```
GET    /health                      # Health check → {"status": "ok", "db": "ok"}
GET    /api/dashboard               # Unified dashboard data
```

---

## UI Screens

### 1. Dashboard (`/`)
- **Header:** Vessel name, homeport, current date, weather widget (optional)
- **Alert banner:** Overdue maintenance items (red), expiring documents (amber)
- **Quick stats cards:** Open Defects | Due in 30 days | Low Stock Parts | Active Checklists
- **Recent activity feed:** Last 10 maintenance entries, defects, checklist runs
- **Upcoming maintenance table:** Next 10 items due (sorted by date/hours)
- **Quick actions:** Log Hours | New Defect | Run Checklist | Log Maintenance

### 2. Equipment Register (`/equipment`)
- **Category sidebar:** Propulsion | Electrical | Navigation | Safety | Mechanical | Hotel Systems
- **Equipment list:** Card or table view; status badge (operational/monitor/offline)
- **Equipment detail page:**
  - Specs panel (make, model, S/N, install date, location)
  - Maintenance tab: scheduled tasks + history
  - Documents tab: linked manuals, invoices
  - Defects tab: open issues linked to this equipment
  - Parts tab: associated spares

### 3. Maintenance Schedule (`/maintenance`)
- **View toggle:** Calendar | List | Gantt-lite (by month)
- **Filter bar:** Status (overdue/due soon/upcoming) | Category | Assigned vendor
- **List view table:** Equipment | Task | Last Done | Next Due | Interval | Priority | Action
- **"Mark Complete" modal:** Date, engine hours, cost, parts used, notes, performed by
- **Add Task modal:** Full form with interval type/value, vendor, estimated cost

### 4. Defect Log — Squawk Board (`/defects`)
- **Kanban columns:** Open | In Progress | Resolved | Deferred
- **Each card:** Title, equipment, severity badge, date, assigned vendor
- **New Defect form:** Equipment (searchable), title, description, severity, photos upload
- **Defect detail:** Full history, cost tracking, resolution notes, linked documents

### 5. Maintenance History (`/history`)
- **Timeline view:** Reverse chronological, grouped by date
- **Filter:** Equipment | Date range | Vendor | Cost range
- **Export:** CSV download of filtered results
- **Entry detail:** Full work record, parts used, cost, who performed it

### 6. Parts Inventory (`/parts`)
- **Table:** Part | Equipment | Qty on Hand | Min Qty | Unit Cost | Vendor | Location
- **Low Stock badge:** Highlight items below minimum
- **Adjust stock modal:** +/- with reason (used, received, expired)
- **Filter:** Equipment | Vendor | Low stock only
- **Vendor links:** Clickable vendor name → vendor detail page

### 7. Checklists (`/checklists`)
- **Template library:** Departure | Arrival | Weekly | Safety Drill | Passage
- **"Run Checklist" button:** Creates a new run instance
- **Run view:** Interactive checklist with check-off, notes per item
- **Run history:** Completed runs with date, who, completion %
- **Template editor:** Drag-and-drop item ordering, add/remove items

### 8. Documents (`/documents`)
- **Category tabs:** Manuals | Certificates | Insurance | Invoices | Photos | Other
- **Card grid or table:** Filename, category, equipment, expiry date (if set)
- **Upload modal:** File picker, title, category, linked equipment, expiry date
- **Expiring banner:** Yellow alert for docs expiring in 90 days
- **Preview:** PDF viewer in-browser (for PDFs)

### 9. Engine Hours (`/engine-hours`)
- **Current readings:** Port engine, Starboard engine, Generator (large display)
- **Log entry form:** Engine, hours, date, notes
- **History table:** All readings, delta hours since last entry
- **Maintenance trigger view:** Tasks that become due based on current hours

### 10. Vendors (`/vendors`)
- **List:** Name, category, phone, email, website
- **Detail page:** Contact info, linked maintenance history (work done by this vendor)

### 11. Settings (`/settings`)
- **Vessel info editor**
- **User management** (add/remove crew)
- **Equipment categories editor**
- **Notification preferences** (email alerts for overdue items — Phase 2)
- **Data export:** Full database dump as JSON or CSV

---

## Seed Data — Princess F50 Equipment & Maintenance Intervals

### Equipment Categories (seed)
```
1. Propulsion & Drives
2. Electrical Systems
3. Navigation & Electronics
4. Safety Equipment
5. Mechanical Systems
6. Hotel & Comfort Systems
7. Deck & Hull
8. Safety & Emergency
```

### Equipment Register (seed) — Princess F50 specific

```
PROPULSION & DRIVES
───────────────────
- Port Volvo Penta D11 / IPS700 (725hp) | S/N: [TBD] | Engine Room - Port
- Stbd Volvo Penta D11 / IPS700 (725hp) | S/N: [TBD] | Engine Room - Starboard
- Port IPS Drive Unit | Engine Room - Port
- Stbd IPS Drive Unit | Engine Room - Starboard
- Aquamatic IPS Control System

ELECTRICAL SYSTEMS
──────────────────
- Onan/Cummins MDKDW Generator | Engine Room
- Shore Power System (50A) | Transom
- Battery Bank - Engine Start (Port) | Engine Room
- Battery Bank - Engine Start (Stbd) | Engine Room
- Battery Bank - House | Engine Room
- Battery Bank - Generator Start | Engine Room
- Battery Charger / Inverter | Engine Room
- DC Distribution Panel | Helm Station
- AC Distribution Panel | Salon

NAVIGATION & ELECTRONICS
─────────────────────────
- Garmin GMX 1220 MFD (Chartplotter) | Helm Station
- VHF Radio (primary) | Helm Station
- VHF Radio (secondary/handheld) | Navigation Station
- AIS Transponder | Navigation Station
- Radar | Mast
- Autopilot (Garmin/Volvo) | Helm
- Depth/Speed/Wind Instruments | Helm
- EPIRB | Navigation Station
- MOB Alarm System | Helm

MECHANICAL SYSTEMS
──────────────────
- Bow Thruster (electric) | Bow
- Stern Thruster (electric/hydraulic) | Stern
- Hydraulic Power Unit | Engine Room
- Watermaker (Spectra/Katadyn) | Engine Room
- Fuel System (twin tanks, crossfeed) | Engine Room
- Freshwater System & Pressure Pump | Engine Room
- Blackwater System & Holding Tank | Engine Room
- Bilge Pump - Engine Room (Auto) | Engine Room
- Bilge Pump - Bow Compartment (Auto) | Bow
- Bilge Pump - Stern Compartment (Auto) | Stern
- Sea Cocks (engine raw water intakes) | Engine Room

HOTEL & COMFORT SYSTEMS
────────────────────────
- Marine A/C System - Salon | Salon
- Marine A/C System - Master Cabin | Master Cabin
- Marine A/C System - Guest Cabin | Guest Cabin
- Seawater Cooling Pump (A/C) | Engine Room
- Refrigerator / Icemaker | Galley
- Diesel Heating System (if fitted) | Engine Room
- Hot Water Heater | Engine Room

DECK & HULL
───────────
- Windlass (Lewmar/Maxwell) | Foredeck
- Anchor & Chain | Foredeck
- Running Rigging (bimini, covers) | Deck
- Davits / Tender System | Stern
- Tender (RIB/inflatable) | Stern Platform
- Outboard Motor (tender) | Stern

SAFETY & EMERGENCY
───────────────────
- Life Raft (6-person) | Cockpit locker
- EPIRB (406 MHz) | Navigation Station
- Flares Kit | Navigation Station
- Fire Extinguishers (x4) | Multiple
- First Aid Kit | Salon
- Life Jackets / PFDs (x6) | Cockpit locker
- Safety Harnesses (x4) | Cockpit locker
- Throw Ring / MOB Equipment | Cockpit
```

### Maintenance Tasks — Standard Marine Intervals (seed)

#### Volvo Penta D11 / IPS700 (per engine — apply to both)
```
Task                              | Interval      | Priority
──────────────────────────────────|───────────────|─────────
Engine oil & filter change        | 250 hours     | Critical
Fuel filter (primary) replace     | 250 hours     | Critical
Fuel filter (secondary) replace   | 500 hours     | High
Raw water impeller replacement    | 300 hours     | Critical
Serpentine/drive belt inspect     | 500 hours     | High
Serpentine/drive belt replace     | 2 years       | High
Coolant flush & fill              | 2 years       | High
Heat exchanger zincs replace      | 6 months      | High
Injector service                  | 2000 hours    | High
Valve clearance check             | 1000 hours    | High
Turbocharger inspect              | 1000 hours    | Normal
Air filter replace                | 500 hours     | Normal
Engine mounts inspect             | 12 months     | Normal
Throttle/shift cables inspect     | 12 months     | Normal
Engine alignment check            | 24 months     | Normal
Volvo VODIA diagnostic scan       | 12 months     | Normal
```

#### IPS Drive Units
```
Task                              | Interval      | Priority
──────────────────────────────────|───────────────|─────────
IPS drive oil change              | 250 hours     | Critical
IPS drive oil (gear) change       | 1000 hours    | High
IPS drive zincs inspect/replace   | 6 months      | Critical
IPS bellows inspect               | 12 months     | High
IPS bellows replace               | 3 years       | High
IPS drive alignment check         | 24 months     | High
IPS U-joint service               | 1000 hours    | High
Pod seals inspect                 | 6 months      | Normal
Propeller inspect & balance       | 12 months     | Normal
Propeller zinc replace            | 6 months      | Critical
```

#### Generator (Onan/Cummins MDKDW)
```
Task                              | Interval      | Priority
──────────────────────────────────|───────────────|─────────
Generator oil & filter change     | 150 hours     | Critical
Generator fuel filter replace     | 250 hours     | High
Raw water impeller replace        | 300 hours     | Critical
Generator zincs replace           | 6 months      | High
Load test (under load)            | 6 months      | Normal
Carbon brushes inspect            | 12 months     | Normal
Coolant check                     | 6 months      | Normal
```

#### Watermaker
```
Task                              | Interval      | Priority
──────────────────────────────────|───────────────|─────────
Pre-filter (sediment) replace     | 3 months      | High
Carbon pre-filter replace         | 6 months      | High
Membrane flush (pickling)         | If unused 30d | High
Membrane replace                  | 3-5 years     | High
High-pressure pump oil change     | 12 months     | Normal
System flush with fresh water     | After each use| Normal
Clark Pump inspect                | 24 months     | Normal
```

#### Marine A/C System
```
Task                              | Interval      | Priority
──────────────────────────────────|───────────────|─────────
Seawater strainer clean           | Monthly       | High
Air filter clean/replace          | 3 months      | Normal
Evaporator coil inspect/clean     | 12 months     | Normal
Refrigerant level check           | 12 months     | Normal
Seawater pump impeller replace    | 2 years       | High
Condensate drain clear            | 6 months      | Normal
Zinc anode (heat exchanger) replace| 6 months     | High
```

#### Thrusters (Bow & Stern)
```
Task                              | Interval      | Priority
──────────────────────────────────|───────────────|─────────
Thruster zinc replace             | 6 months      | Critical
Thruster fluid level check        | 6 months      | High
Thruster fluid change             | 24 months     | High
Brushes/motor inspect             | 24 months     | Normal
Propeller inspect                 | 12 months     | Normal
```

#### Electrical Systems
```
Task                              | Interval      | Priority
──────────────────────────────────|───────────────|─────────
Battery voltage/capacity test     | 6 months      | High
Battery terminal clean/tighten    | 6 months      | Normal
Shore power cord/plug inspect     | 6 months      | Normal
DC panel connections inspect      | 12 months     | Normal
AC panel connections inspect      | 12 months     | Normal
Bilge pump function test          | Monthly       | Critical
Bilge pump float switch test      | Monthly       | Critical
Inverter/charger self-test        | 6 months      | Normal
```

#### Safety Equipment
```
Task                              | Interval      | Priority
──────────────────────────────────|───────────────|─────────
Life raft inspection/repack       | 3 years       | Critical
EPIRB registration verify         | 12 months     | Critical
EPIRB battery replace             | Per mfr date  | Critical
Flares replace (expiry check)     | Per expiry    | Critical
Fire extinguisher service         | 12 months     | Critical
Fire extinguisher replace         | 6 years       | Critical
Life jacket inflation test        | 12 months     | Critical
Life jacket hydrostatic test      | 5 years       | Critical
Smoke/CO detector test            | Monthly       | Critical
Smoke/CO detector replace         | 7 years       | Critical
```

#### Bilge Systems
```
Task                              | Interval      | Priority
──────────────────────────────────|───────────────|─────────
Bilge pump test (engine room)     | Monthly       | Critical
Bilge pump test (bow)             | Monthly       | Critical
Bilge pump test (stern)           | Monthly       | Critical
Bilge clean (oil/debris)          | 6 months      | High
Bilge alarm test                  | Monthly       | Critical
```

#### Hull & Running Gear
```
Task                              | Interval      | Priority
──────────────────────────────────|───────────────|─────────
Hull zinc replace (full set)      | 12 months     | Critical
Hull zinc inspect                 | 6 months      | High
Antifouling bottom paint          | 12 months     | High
Seacock operate/grease            | 6 months      | High
Through-hull inspect              | 12 months     | High
Anchor chain inspect/mark         | 12 months     | Normal
Windlass service                  | 12 months     | Normal
```

#### Navigation Electronics
```
Task                              | Interval      | Priority
──────────────────────────────────|───────────────|─────────
Chartplotter software update      | 12 months     | Normal
Radar calibrate/test              | 12 months     | Normal
VHF radio DSC test                | 12 months     | High
EPIRB registration renewal        | 2 years       | Critical
AIS transponder verify            | 12 months     | High
GPS antenna inspect               | 12 months     | Normal
```

### Vendors (seed)
```
1. Marea Marine           | category: mechanic    | Sausalito, CA
2. Marine Parts Source    | category: parts       | website: marinepartssource.com
3. Helmut's Marine Service| category: mechanic    | Sausalito, CA
4. Harbor West Yacht Club | category: marina      | Sausalito, CA
5. West Marine            | category: chandlery   | Sausalito, CA | website: westmarine.com
6. Volvo Penta of Americas| category: parts       | website: volvopenta.com
7. Northern California Diesel | category: mechanic | Northern CA
```

---

## File Structure

```
yacht-manager/
├── Dockerfile
├── docker-compose.yml
├── docker-compose.dev.yml          # with volume mounts for hot reload
├── railway.json
├── railway.toml
├── .env.example
├── .gitignore
├── requirements.txt
├── alembic.ini
│
├── app/
│   ├── main.py                     # FastAPI app factory, middleware, startup
│   ├── config.py                   # Settings via pydantic-settings
│   ├── database.py                 # SQLAlchemy async engine + session
│   ├── auth.py                     # JWT auth, password hashing
│   ├── dependencies.py             # get_db, get_current_user
│   │
│   ├── models/                     # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── vessel.py
│   │   ├── equipment.py
│   │   ├── maintenance.py
│   │   ├── defect.py
│   │   ├── parts.py
│   │   ├── checklist.py
│   │   ├── document.py
│   │   ├── engine_hours.py
│   │   └── vendor.py
│   │
│   ├── schemas/                    # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── vessel.py
│   │   ├── equipment.py
│   │   ├── maintenance.py
│   │   ├── defect.py
│   │   ├── parts.py
│   │   ├── checklist.py
│   │   ├── document.py
│   │   ├── engine_hours.py
│   │   └── vendor.py
│   │
│   ├── routers/                    # FastAPI route handlers
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── vessel.py
│   │   ├── equipment.py
│   │   ├── maintenance.py
│   │   ├── history.py
│   │   ├── defects.py
│   │   ├── parts.py
│   │   ├── checklists.py
│   │   ├── documents.py
│   │   ├── engine_hours.py
│   │   ├── vendors.py
│   │   └── dashboard.py
│   │
│   ├── services/                   # Business logic layer
│   │   ├── maintenance_service.py  # Due-date calculations, completion logic
│   │   ├── alert_service.py        # Dashboard alerts aggregation
│   │   └── document_service.py     # File handling, future S3
│   │
│   ├── seed/                       # Seed data
│   │   ├── seed.py                 # Main seed runner
│   │   ├── f50_equipment.py        # Princess F50 equipment list
│   │   ├── f50_maintenance.py      # Standard maintenance intervals
│   │   ├── checklists.py           # Standard checklist templates
│   │   └── vendors.py              # Local vendors
│   │
│   └── static/                     # Frontend assets
│       ├── css/
│       │   ├── main.css            # Base styles
│       │   └── components.css      # Cards, tables, modals
│       ├── js/
│       │   ├── main.js             # App bootstrap, auth
│       │   ├── htmx.min.js         # HTMX library
│       │   ├── dashboard.js
│       │   ├── equipment.js
│       │   ├── maintenance.js
│       │   ├── defects.js
│       │   ├── checklists.js
│       │   ├── documents.js
│       │   └── parts.js
│       └── img/
│           └── princess-f50.jpg    # Vessel silhouette
│
├── templates/                      # Jinja2 HTML templates
│   ├── base.html                   # Layout, nav, sidebar
│   ├── login.html
│   ├── dashboard.html
│   ├── equipment/
│   │   ├── list.html
│   │   └── detail.html
│   ├── maintenance/
│   │   ├── list.html
│   │   └── complete_modal.html
│   ├── defects/
│   │   ├── board.html
│   │   └── detail.html
│   ├── history/
│   │   └── timeline.html
│   ├── parts/
│   │   └── inventory.html
│   ├── checklists/
│   │   ├── library.html
│   │   └── run.html
│   ├── documents/
│   │   └── library.html
│   └── vendors/
│       └── list.html
│
├── migrations/                     # Alembic migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 001_create_extensions.py   # uuid-ossp, pgcrypto -- FIRST
│       └── 002_initial_schema.py      # All tables
│
└── tests/
    ├── conftest.py                 # Test DB setup, fixtures
    ├── test_auth.py
    ├── test_equipment.py
    ├── test_maintenance.py
    ├── test_defects.py
    └── test_parts.py
```

---

## Dockerfile

```dockerfile
FROM python:3.12-slim

# System deps
RUN apt-get update && apt-get install -y \
    libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 yacht && chown -R yacht:yacht /app
USER yacht

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

EXPOSE 8000

# Run migrations then start server
CMD alembic upgrade head && \
    python -m app.seed.seed && \
    uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

---

## docker-compose.yml

```yaml
version: "3.9"

services:
  web:
    build: .
    ports:
      - "${PORT:-8000}:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://yacht:yacht@db:5432/yachtmanager
      - SECRET_KEY=${SECRET_KEY:-changeme-in-production-32chars}
      - ADMIN_EMAIL=${ADMIN_EMAIL:-eric@example.com}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD:-changeme}
      - CORS_ORIGINS=${CORS_ORIGINS:-http://localhost:8000}
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: yachtmanager
      POSTGRES_USER: yacht
      POSTGRES_PASSWORD: yacht
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U yacht -d yachtmanager"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:
```

---

## requirements.txt

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy[asyncio]==2.0.36
asyncpg==0.29.0
alembic==1.13.3
pydantic-settings==2.5.2
pydantic[email]==2.9.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.12
jinja2==3.1.4
aiofiles==24.1.0
httpx==0.27.2
pytest==8.3.3
pytest-asyncio==0.24.0
```

---

## railway.json

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "./Dockerfile"
  },
  "deploy": {
    "healthcheckPath": "/health",
    "healthcheckTimeout": 30,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

---

## .env.example

```bash
# Copy to .env for local dev -- NEVER commit .env to git
PORT=8000
DATABASE_URL=postgresql+asyncpg://yacht:yacht@localhost:5432/yachtmanager
SECRET_KEY=your-32-character-random-secret-key-here
ADMIN_EMAIL=eric@brownfamily.com
ADMIN_PASSWORD=changeme-use-strong-password
CORS_ORIGINS=http://localhost:8000
UPLOAD_MAX_MB=50
```

---

## Implementation Phases

### Phase 1: Foundation & Docker (Week 1)
**Goal:** Running skeleton deployed to Railway with auth and vessel setup.

- [ ] **Task 1.1** — Project skeleton
  - Init git repo, `app/` structure, `requirements.txt`, `.gitignore`
  - `.env.example`, `Dockerfile`, `docker-compose.yml`, `railway.json`
  - **Agent:** Coder | **Acceptance:** `docker build` succeeds

- [ ] **Task 1.2** — Database setup
  - SQLAlchemy async engine, Alembic init
  - Migration 001: CREATE EXTENSION (uuid-ossp) — separate transaction
  - Migration 002: All tables from schema above
  - **Agent:** Coder | **Acceptance:** `alembic upgrade head` runs clean

- [ ] **Task 1.3** — Auth system
  - JWT login/logout, password hashing with bcrypt
  - Admin user created on startup from env vars
  - Protected routes with `get_current_user` dependency
  - **Agent:** Coder | **Acceptance:** `POST /api/auth/login` returns JWT

- [ ] **Task 1.4** — Base UI layout
  - Jinja2 base template with sidebar nav, HTMX loaded
  - Login page, redirect on JWT
  - Marine-themed design (navy/white/gold palette)
  - **Agent:** Coder | **Acceptance:** Login page renders, nav works

- [ ] **Task 1.5** — Railway deployment
  - Set all env vars in Railway dashboard
  - Deploy → verify `/health` returns 200
  - **Agent:** Coder | **Acceptance:** Live URL accessible

### Phase 2: Core Features (Weeks 2–3)
**Goal:** Equipment register, maintenance scheduling, defect log live.

- [ ] **Task 2.1** — Equipment Register
  - All CRUD endpoints + Jinja2 templates
  - Category sidebar, status badges
  - Seed data: F50 equipment list (all components above)
  - **Agent:** Coder | **Acceptance:** Equipment list renders with F50 data

- [ ] **Task 2.2** — Maintenance Scheduling
  - Maintenance task CRUD
  - Due-date calculation logic (hours vs calendar intervals)
  - "Mark Complete" flow: updates `last_done_*`, calculates `next_due_*`
  - Overdue/upcoming filter queries
  - Seed data: all intervals from schema above
  - **Agent:** Coder | **Acceptance:** Overdue tasks show on dashboard

- [ ] **Task 2.3** — Defect Log (Squawk Board)
  - Defect CRUD + Kanban board UI
  - Severity color coding, status transitions
  - Link defects to equipment
  - **Agent:** Coder | **Acceptance:** Can create, update, resolve defects

- [ ] **Task 2.4** — Maintenance History
  - History log with timeline view
  - Created automatically when task completed
  - CSV export
  - **Agent:** Coder | **Acceptance:** History entry created on task completion

- [ ] **Task 2.5** — Engine Hours Tracking
  - Log hours per engine, per date
  - Current hours displayed on dashboard
  - Maintenance tasks show hours-to-next-service
  - **Agent:** Coder | **Acceptance:** Hours feed into maintenance due calculations

### Phase 3: Inventory, Checklists & Documents (Weeks 3–4)
**Goal:** Full feature parity with Seahub core.

- [ ] **Task 3.1** — Parts Inventory
  - Full CRUD, low-stock alerts, adjust quantity modal
  - Seed: common F50 spares (filters, impellers, zincs, belts)
  - **Agent:** Coder | **Acceptance:** Low-stock items flagged on dashboard

- [ ] **Task 3.2** — Checklists
  - Template library + run instances
  - Interactive check-off UI
  - Standard templates seeded: Departure, Arrival, Weekly, Safety Drill
  - **Agent:** Coder | **Acceptance:** Can complete a departure checklist

- [ ] **Task 3.3** — Document Storage
  - File upload (PDF, images), store as BYTEA in DB
  - Category tabs, download, expiry tracking
  - Expiring documents alert on dashboard
  - **Agent:** Coder | **Acceptance:** Can upload engine manual, view it

- [ ] **Task 3.4** — Vendors
  - Vendor CRUD, link to maintenance history
  - **Agent:** Coder | **Acceptance:** Vendor list shows seeded vendors

### Phase 4: Dashboard & Polish (Week 4)
**Goal:** Production-quality UX with smart alerting.

- [ ] **Task 4.1** — Dashboard
  - Unified dashboard with alert banner, stats cards, upcoming maintenance table
  - Recent activity feed
  - Engine hours widget
  - **Agent:** Coder | **Acceptance:** Dashboard shows live data from all modules

- [ ] **Task 4.2** — Search & Filters
  - Global search across equipment, defects, history
  - HTMX-powered live filter on all list views
  - **Agent:** Coder | **Acceptance:** Search returns relevant results

- [ ] **Task 4.3** — Mobile Responsiveness
  - Responsive CSS for use on bridge or below deck on tablet/phone
  - Touch-friendly checklist interaction
  - **Agent:** Coder | **Acceptance:** Works on iPhone (Sausalito dockside use)

- [ ] **Task 4.4** — Testing suite
  - Pytest fixtures with test DB
  - Tests for auth, equipment CRUD, maintenance completion flow
  - Docker container test run
  - **Agent:** Quality | **Acceptance:** All tests pass in Docker

### Phase 5: Future Enhancements (Backlog)
- [ ] Email alerts for overdue maintenance (SendGrid integration)
- [ ] S3/Dropbox document storage (move off BYTEA for large files)
- [ ] Voyage/trip log (departure/arrival, fuel, nm logged)
- [ ] Fuel consumption tracking
- [ ] Cost reporting (annual maintenance spend by category)
- [ ] Multi-vessel support
- [ ] Offline PWA mode for use without connectivity
- [ ] Integration with Volvo Penta Connect for automatic engine hours sync

---

## Edge Case Checklist

- [x] **Error handling:** All DB ops in try/except; FastAPI exception handlers for 404/422/500
- [x] **Auth expiry:** JWT expiry set to 24h; frontend redirects to login on 401
- [x] **Null/empty inputs:** Pydantic validators on all schemas; Optional fields handled
- [x] **Large file uploads:** UPLOAD_MAX_MB env var enforced; streaming for large PDFs
- [x] **Concurrent access:** SQLAlchemy async sessions; no in-memory state
- [x] **Partial failure:** Maintenance completion is atomic (task + history in one transaction)
- [x] **DB extension ordering:** Extension migration runs first in its own transaction
- [x] **Service startup ordering:** Docker Compose healthcheck ensures DB ready before web
- [x] **railway.json vs Dockerfile CMD conflicts:** CMD in Dockerfile only; railway.json = build config only
- [x] **.env pre-commit check:** `.env` and `.env.*` in `.gitignore`; verify before first commit
- [x] **Hours-based maintenance:** Guard against null `engine_hours` when calculating next due
- [x] **Document BYTEA size:** Warn if file >50MB; Phase 2 moves to S3
- [x] **Seed idempotency:** Seed script checks if data already exists before inserting

---

## Success Criteria

- [ ] `docker build -t yacht-manager .` succeeds in < 3 minutes
- [ ] `docker run -p 8000:8000 yacht-manager` starts without errors
- [ ] `curl localhost:8000/health` returns `{"status": "ok", "db": "ok"}`
- [ ] All 50+ Princess F50 equipment items visible in Equipment Register
- [ ] All standard maintenance intervals seeded and showing on schedule
- [ ] Can log a completed engine oil change and see it in history
- [ ] Can create, assign, and resolve a defect
- [ ] Can run a Departure Checklist end-to-end
- [ ] Deploys to Railway with zero manual file copies
- [ ] No `/Users/...` or host paths anywhere in application code
- [ ] All tests pass inside Docker container

---

## Rollback Plan

1. Railway keeps previous deployment snapshots — instant rollback via Railway dashboard
2. Database migrations use Alembic — `alembic downgrade -1` reverts last schema change
3. Seed data is idempotent — safe to re-run; no data destruction
4. `.env` backed up in 1Password vault (not git)

---

## Cross-Review Notes
**Date:** 2026-03-18
**Review loop:** Deferred — single-user project, well-defined domain, comprehensive schema. Implement directly.

### Key Architectural Risks (Self-Review)
- **CRITICAL:** BYTEA document storage will hit Railway's 1GB PostgreSQL limit quickly if storing manuals and photos. Enforce 50MB upload cap strictly; plan S3 migration as Phase 5 priority #1.
- **IMPORTANT:** Maintenance due-date logic must handle: (a) equipment with no hours logged yet, (b) tasks with both hour AND calendar intervals, (c) tasks where hours are unknown. Use calendar-only as safe fallback.
- **NICE-TO-HAVE:** Add `/api/export/backup` endpoint that dumps full DB as JSON — important for a CFO who needs an audit-ready data export story before going to production.

---

*Plan authored by Architect (OpenClaw Planning Agent) | 2022 Princess F50 | Sausalito, CA*
*Next step: Hand to Coder agent with Phase 1 Task 1.1*
