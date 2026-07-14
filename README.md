# Open Source APEX Equivalent

This project aims to build an open-source equivalent of Oracle APEX (Application Express) as described in the technical specification [rapport_apex_architecture.docx](./rapport_apex_architecture.docx).

## Implementation Plan

See [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) for a detailed phased approach to building this application.

## Project Structure

```
miniui/
├── backend/                 # Python/FastAPI application
│   ├── app/
│   │   ├── api/             # API endpoints
│   │   ├── core             # Core rendering engine
│   │   ├── db               # Database models and session management
│   │   ├── schemas          # Pydantic models for metadata
│   │   └── utils            # Utility functions
│   ├── tests/               # Backend tests
│   ├── alembic/             # Database migrations
│   ├── requirements.txt
│   └── main.py              # FastAPI entry point
├── frontend/                # React visual builder
│   ├── public
│   └── src/
│       ├── components       # Reusable UI components
│       ├── pages            # Builder pages
│       ├── hooks            # Custom hooks
│       └── utils            # Utility functions
├── docs/                    # Documentation
├── scripts/                 # Utility scripts
├── docker-compose.yml       # For local development (PostgreSQL, etc.)
└── README.md
```

## Getting Started

1. Clone this repository
2. Review the implementation plan in `IMPLEMENTATION_PLAN.md`
3. Refer to the technical specification in `rapport_apex_architecture.docx`
4. Begin implementation following the phased approach outlined in the plan

## Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL 15+
- Docker (optional, for development environment)

## License

[To be determined]
