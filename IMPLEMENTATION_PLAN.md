# Implementation Plan: Open Source APEX Equivalent

Based on the technical specification in `rapport_apex_architecture.docx`, this document outlines a phased implementation plan to build an open-source equivalent of Oracle APEX from scratch.

## Phase 0: Project Setup and Foundations

### 0.1 Environment Setup
- Install Python 3.12+, Node.js 18+, PostgreSQL 15+
- Set up development tools: Git, Docker (optional for DB), IDE
- Create project repository with initial structure

### 0.2 Project Structure
```
/miniui
  /backend          # Python/FastAPI application
    /app
      /api          # API endpoints
      /core         # Core rendering engine
      /db           # Database models and session management
      /schemas      # Pydantic models for metadata
      /utils        # Utility functions
    /tests          # Backend tests
    alembic/        # Database migrations
    requirements.txt
    main.py         # FastAPI entry point
  /frontend         # React visual builder
    /public
    /src
      /components   # Reusable UI components
      /pages        # Builder pages
      /hooks        # Custom hooks
      /utils        # Utility functions
    package.json
  /docs             # Documentation
  /scripts          # Utility scripts
  docker-compose.yml# For local development (PostgreSQL, etc.)
  README.md
```

### 0.3 Initial Configuration
- Initialize Git repository
- Set up Python virtual environment and install dependencies (FastAPI, SQLAlchemy, psycopg2-binary, python-dotenv, etc.)
- Set up Node.js project for frontend (React, TypeScript, Material-UI or similar UI library)
- Configure PostgreSQL database and connection settings
- Create basic Docker Compose for local development (PostgreSQL, backend, frontend)

## Phase 1: Metadata Schema Design

### 1.1 Core Metadata Tables
Design PostgreSQL tables to store application definitions (mirroring APEX's wwv_flow_* tables):
- `apex_applications`: Application-level metadata (ID, name, alias, etc.)
- `apex_pages`: Page definitions (ID, name, alias, application ID)
- `apex_regions`: Region definitions on pages (type: report, form, chart, etc.)
- `apex_page_items`: Form items (text, select, date, etc.) with properties
- `apex_page_processes`: Processes (PL/SQL equivalent: server-side logic)
- `apex_validations`: Validation rules for items
- `apex_lovs`: Lists of values (for select items)
- `apex_session_state`: Key-value storage for session state
- `apex_workspace_users`: User management (simplified for initial version)

### 1.2 Database Migrations
- Use Alembic for schema versioning
- Create initial migration for metadata tables
- Define relationships and constraints
- Add indexes for performance

## Phase 2: Core Rendering Engine

### 2.1 Page Show Logic (GET)
Implement `show_page` function in backend:
- Retrieve page definition from metadata tables
- Initialize session state for the page
- Process computations (if any)
- Render regions and items based on metadata
- Generate HTML, CSS, and JavaScript output
- Implement basic region types: 
  - Static Content (HTML)
  - Report (SQL query based grid)
  - Form (based on page items)

### 2.2 Page Accept Logic (POST)
Implement `accept_page` function:
- Retrieve submitted item values
- Update session state in database
- Process validations
- Execute processes (INSERT/UPDATE/DELETE logic)
- Handle branching (success/failure URLs)
- Return appropriate response (redirect or AJAX response)

### 2.3 Session State Management
- Create service for getting/setting session state values
- Tie session state to user session (using browser cookies or tokens)
- Implement automatic cleanup of old sessions

## Phase 3: Basic Component Implementation

### 3.1 Item Types
Implement rendering for basic item types:
- Text Field
- Textarea
- Select List (with LOV support)
- Checkbox
- Radio Group
- Date Picker
- Hidden Item
- Display Only (for read-only values)

### 3.2 Region Types
Implement basic region types:
- Static Content: Renders HTML/CSS from metadata
- Report: 
  - Defined by SQL query in metadata
  - Supports basic filtering, sorting, pagination
  - Renders as HTML table
- Form: 
  - Based on page items metadata
  - Supports INSERT, UPDATE, DELETE operations
  - Includes validation and processing

### 3.3 Processes
Implement basic process types:
- SQL Script: Execute arbitrary SQL
- PL/SQL equivalent: Python functions or predefined operations
- Reset/Pagination: Standard APEX processes

## Phase 4: Visual Builder (Frontend)

### 4.1 Builder Interface
Create React application for building ApexOS applications:
- Dashboard: List of applications
- Application Builder: 
  - Application properties editor
  - Page manager (add/remove pages)
- Page Builder:
  - Drag-and-drop interface for placing regions
  - Region configuration sidebar
  - Item editor (for form items)
  - Process and validation editors

### 4.2 Metadata Synchronization
- Frontend communicates with backend REST API to save/load application metadata
- Implement CRUD operations for:
  - Applications
  - Pages
  - Regions
  - Items
  - Processes
  - Validations
- Real-time preview of the application being built

### 4.3 Code Generation (Optional)
- Allow exporting application as standalone Python/FastAPI project
- Or keep metadata-driven approach where builder and runtime are coupled

## Phase 5: Security Implementation

### 5.1 Authentication
- Implement database-based authentication (username/password stored in `apex_workspace_users`)
- Add support for OAuth2 (Google, GitHub) as stretch goal
- Session management with secure cookies

### 5.2 Authorization
- Role-based access control (RBAC) for builder and runtime
- Application-level editing permissions
- Page-level access control (public/authenticated)

### 5.3 Security Features
- CSRF protection for all state-changing operations
- Input sanitization to prevent XSS
- Content Security Policy headers
- Secure session handling

## Phase 6: REST API Integration

### 6.1 REST Data Sources Equivalent
- Allow defining REST API endpoints in metadata
- Implement server-side calls to external REST services
- Support for GET, POST, PUT, DELETE
- JSON response parsing and mapping to page items/regions

### 6.2 Built-in REST Endpoints
- Provide CRUD REST API for applications (for external consumption)
- Secure these endpoints with same authentication system

## Phase 7: Testing and Quality Assurance

### 7.1 Backend Testing
- Unit tests for core rendering functions
- Integration tests for show_page/accept_page flows
- Database migration tests
- API endpoint tests

### 7.2 Frontend Testing
- Unit tests for React components
- Integration tests for builder workflows
- End-to-end tests for application creation and execution

### 7.3 Performance Testing
- Load testing for concurrent users
- Database query optimization
- Caching strategies for metadata

## Phase 8: Deployment and Documentation

### 8.1 Deployment Guide
- Docker Compose for development
- Helm chart for Kubernetes
- Environment variable configuration
- Database initialization scripts

### 8.2 Documentation
- User guide for the visual builder
- API reference for developers
- Contribution guidelines
- Release notes

### 8.3 Initial Release (MVP)
- Ability to create simple data-driven applications
- Basic form and report regions
- Session state management
- Visual builder for creating pages
- Database authentication

## Phase 9: Stretch Goals (Post-MVP)

### 9.1 Advanced Component Types
- Interactive Grid (editable report)
- Charts (using Chart.js or similar)
- Trees
- Calendars
- Maps
- Plugins system for community components

### 9.2 Advanced Features
- Dynamic Actions (client-side JavaScript)
- Authorization schemes
- Themeable UI (CSS variables/themes)
- Debug mode and error logging
- Application export/import (JSON)

### 9.3 Performance Optimizations
- Metadata caching layer
- Database connection pooling
- Async processing for long-running tasks
- CDN for static assets

## Implementation Sequence Summary

1. Setup project and dependencies
2. Design and implement metadata schema
3. Build core rendering engine (show/accept)
4. Implement basic item and region types
5. Create visual builder frontend
6. Add security features
7. Implement REST data sources
8. Write tests and documentation
9. Deploy and gather feedback
10. Iterate on advanced features

This plan provides a structured approach to building an open-source APEX equivalent, focusing on delivering a functional MVP first before expanding to more complex features. Each phase builds upon the previous one, allowing for incremental development and testing.

---
*Plan created based on the specification in rapport_apex_architecture.docx*