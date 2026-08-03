# Frontend - ApexOS Builder

This is the React-based visual builder for ApexOS, an open-source Oracle APEX alternative.

## Overview

The frontend provides a comprehensive drag-and-drop interface for building web applications visually, similar to the APEX Application Builder. It allows users to create, design, and preview applications without writing code.

## Features

### Core Functionality
- **Drag-and-drop interface** for placing components and building page layouts
- **Property editors** for configuring components, regions, and pages
- **Preview mode** to test applications as end-users would see them
- **Application and page management** with full CRUD operations
- **Component library** including form items, containers, and display elements

### User Interface
- **Dashboard view** showing all applications with statistics
- **Application builder** for configuring application properties and managing pages
- **Page builder** with canvas for drag-and-drop layout design
- **Property panel** that appears when selecting elements for detailed configuration
- **Responsive design** that works on desktop and tablet screens

### Component Library
**Containers (Regions):**
- Static Content - For HTML/text content, images, and custom markup
- Form - For data entry forms with validation and processing
- Report - For displaying data in tabular, card, or chart formats

**Form Items:**
- Text Field - Single-line text input
- Text Area - Multi-line text input
- Select List - Dropdown selection (with LOV support)
- Checkbox - Boolean true/false selection
- Radio Group - Mutually exclusive option selection
- Date Picker - Calendar-based date selection
- Hidden Item - Non-visible field for storing values
- Display Only - Read-only value display

## Getting Started

### Prerequisites
- Node.js 16+ and npm
- Backend API running (typically on http://localhost:8000)

### Installation
1. Install dependencies: `npm install`
2. Start the development server: `npm start`
3. The application will be available at `http://localhost:3000`

### Production Build
- `npm run build`: Creates optimized production build in `/build` directory

## Project Structure

```
src/
├── components/       # Reusable UI components (buttons, inputs, modals, etc.)
├── pages/            # Application pages/views
│   ├── Dashboard.js        # Application overview and management
│   ├── ApplicationBuilder.js # Application and page configuration
│   ├── PageBuilder.js      # Drag-and-drop page design interface
│   └── Preview.js          # Live preview of built applications
├── App.js            # Main application component with routing
├── App.css           # Global styles and theme
└── index.js          # Entry point
```

## Available Scripts

In the project directory, you can run:

- `npm start`: Runs the app in development mode at http://localhost:3000
- `npm test`: Launches the test runner in interactive watch mode
- `npm run build`: Builds the app for production to the `build` folder
- `npm run eject`: Removes the single build dependency and transfers all configuration files

## API Integration

The frontend communicates with the backend REST API using standard HTTP methods:

### Applications
- `GET /api/applications/` - List all applications
- `POST /api/applications/` - Create new application
- `GET /api/applications/{id}/` - Get specific application
- `PUT /api/applications/{id}/` - Update existing application
- `DELETE /api/applications/{id}/` - Delete application

### Pages
- `GET /api/pages/` - List pages (with optional filtering by application)
- `POST /api/pages/` - Create new page
- `GET /api/pages/{id}/` - Get specific page
- `PUT /api/pages/{id}/` - Update existing page
- `DELETE /api/pages/{id}/` - Delete page

### Runtime
- `GET /app/{application_alias}/{page_number}` - Render and display a page

## Development Notes

This project was created with Create React App and uses:

- **React 18** - For building user interfaces
- **React Router v6** - For client-side routing and navigation
- **React DnD** - For drag-and-drop functionality in the page builder
- **CSS3 with Flexbox/Grid** - For responsive layouts and styling
- **Modern JavaScript ES6+** - For clean, maintainable code

## Future Enhancements

- [ ] Advanced property editors with field validation
- [ ] Visual theme editor and customization
- [ ] Process workflow and automation builder
- [ ] Report and chart configuration wizards
- [ ] Mobile-responsive design preview modes
- [ ] Application import/export functionality
- [ ] User authentication, roles, and permissions
- [ ] Real-time collaborative editing
- [ ] Undo/redo history functionality
- [ ] Keyboard shortcuts for power users
- [ ] Accessibility (WCAG) compliance improvements
- [ ] Code export for standalone applications