# ✈️ Aviation Database System

A comprehensive database system for managing airline operations, including airports, aircraft, flights, ticket sales, and passenger check-ins. Built with PostgreSQL and a RESTful API for programmatic access.

## 📋 Project Overview

This project implements a complete relational database system for an aviation company that operates across multiple international airports. The system handles:

- **Airport Management**: International airports with terminals
- **Fleet Management**: Aircraft with seat configurations (first and second class)
- **Flight Operations**: Scheduled flights with departure and arrival tracking
- **Sales System**: Ticket purchases and reservations
- **Check-in Process**: Seat assignments and boarding passes

## 🗂️ Database Schema

### Core Tables

- **aeroporto** (airport): Airports with 3-letter codes, names, cities, and countries
- **aviao** (aircraft): Aircraft fleet with serial numbers and models
- **assento** (seat): Seat configurations per aircraft (class-based)
- **voo** (flight): Scheduled flights with departure/arrival times
- **venda** (sale): Sales transactions with customer information
- **bilhete** (ticket): Individual tickets with passenger details and pricing

### Key Features

- ✅ **Integrity Constraints**: Enforced business rules through triggers
- ✅ **Data Consistency**: Foreign keys and check constraints
- ✅ **Normalization**: BCNF-compliant schema design
- ✅ **Security**: SQL injection prevention in API layer

## 🛠️ Implementation Components

### 1. Entity-Relationship Model
- Comprehensive E-R diagram representing the aviation domain
- Integrity constraints expressed as business rules
- Complete documentation of relationships and cardinalities

### 2. Relational Model Conversion
- Normalized relational schema (Boyce-Codd Normal Form)
- Primary keys, foreign keys, and unique constraints
- Additional integrity constraints for business logic

### 3. Database Constraints (3 points)

**RI-1**: During check-in, ticket class must match seat class and aircraft must match flight aircraft

**RI-2**: Number of tickets sold per class cannot exceed aircraft capacity for that class

**RI-3**: Sale timestamp must be before departure time of all flights in the purchase

### 4. Data Population (2 points)

The database is populated with realistic data:
- ≥10 European international airports (including cities with multiple airports)
- ≥10 aircraft from ≥3 different models
- ≥5 flights daily (Jan 1 - Jul 31, 2025)
- ≥30,000 tickets across ≥10,000 sales
- Round-trip flight coverage
- Completed check-ins for past flights

### 5. RESTful Web Service (5 points)

A RESTful API built with Flask/Python providing:

#### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List all airports (name and city) |
| GET | `/voos/<partida>/` | Flights departing from airport in next 12h |
| GET | `/voos/<partida>/<chegada>/` | Next 3 available flights between airports |
| POST | `/compra/<voo>/` | Purchase tickets for a flight |
| POST | `/checkin/<bilhete>/` | Check-in and assign seat automatically |

**Features**:
- 🔒 SQL injection prevention
- 🔄 Transaction support for atomicity
- ✅ Proper HTTP methods and status codes
- 📋 Well-structured JSON responses
- ⚠️ Explicit error messages

### 6. Materialized View (2 points)

**estatisticas_voos**: Combines flight information for analytics

```sql
estatisticas_voos(
    no_serie, hora_partida,
    cidade_partida, pais_partida,
    cidade_chegada, pais_chegada,
    ano, mes, dia_do_mes, dia_da_semana,
    passageiros_1c, passageiros_2c,
    assentos_1c, assentos_2c,
    vendas_1c, vendas_2c
)
```

### 7. SQL & OLAP Analytics (5 points)

Advanced SQL queries for business intelligence:

1. **Route Demand Analysis**: Identify busiest routes by average capacity fill
2. **Fleet Management**: Routes covered by all aircraft in the last 3 months
3. **Revenue Analysis**: Multi-dimensional OLAP cube (space × time × class)
4. **Weekly Patterns**: First/second class ratio patterns with drill-down

### 8. Index Optimization (3 points)

Strategic indexing for query performance:
- Analysis with `EXPLAIN ANALYSE`
- Balanced optimization across all analytics queries
- Theoretical justification and practical demonstration

## 🚀 Getting Started

### Prerequisites

```bash
PostgreSQL >= 12
Python >= 3.8
Flask
psycopg2
```

### Database Setup

```bash
# Create database
createdb Aviacao

# Load schema
psql Aviacao < schema.sql

# Populate data
psql Aviacao < data/populate.sql
# or use COPY commands with data files
```

### Running the API

```bash
cd app/
python app.py
```

The API will be available at `http://localhost:5000`

## 📁 Project Structure

```
.
├── E2-report-GG.ipynb       # Jupyter notebook with SQL queries
├── data/
│   ├── populate.sql         # Data insertion script
│   └── *.txt               # Tab-separated data files (alternative)
├── app/
│   ├── app.py              # Flask RESTful API
│   ├── database.py         # Database connection layer
│   └── requirements.txt    # Python dependencies
├── schema.sql              # Database schema creation
└── README.md
```

## 🧪 Testing

### Test Queries

```sql
-- List airports
SELECT nome, cidade FROM aeroporto;

-- Check flights from LIS in next 12 hours
SELECT * FROM voos WHERE partida = 'LIS' 
  AND hora_partida BETWEEN NOW() AND NOW() + INTERVAL '12 hours';
```

### API Testing

```bash
# List airports
curl http://localhost:5000/

# Find flights
curl http://localhost:5000/voos/LIS/

# Purchase tickets
curl -X POST http://localhost:5000/compra/123/ \
  -H "Content-Type: application/json" \
  -d '{"nif": "123456789", "bilhetes": [
    {"passageiro": "John Doe", "classe": false}
  ]}'
```

## 📊 Key Achievements

- ✅ Comprehensive relational database design
- ✅ 30,000+ realistic ticket records
- ✅ RESTful API with 5 functional endpoints
- ✅ Advanced OLAP analytics queries
- ✅ Optimized with strategic indexes
- ✅ Full transaction support and security measures

## 🎓 Academic Context

This project was developed as part of the Database Systems course at Instituto Superior Técnico, Universidade de Lisboa (2024/25).

**Deliverables**:
- Part 1: E-R Model, Relational Model, Relational Algebra
- Part 2: Implementation, API, Analytics, Optimization

## 📚 Technologies Used

- **Database**: PostgreSQL 12+
- **Backend**: Python 3.8+, Flask
- **Data Analysis**: SQL, OLAP operations
- **Tools**: Jupyter Notebook, psycopg2
- **Deployment**: Docker environment

## 🔧 Development Environment

The project uses the [db-workspace](https://github.com/bdist/db-workspace) Docker environment for testing and development.

## 📝 License

This is an academic project. Please respect academic integrity policies if you're a student working on a similar assignment.

## 👥 Contributors

This project was developed by a team of 3 students as part of the course requirements.

---

**Note**: This system demonstrates practical application of database design principles, including normalization, integrity constraints, transaction management, and query optimization for real-world aviation operations.
