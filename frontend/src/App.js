import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';

// Components
import Dashboard from './pages/Dashboard';
import ApplicationBuilder from './pages/ApplicationBuilder';
import PageBuilder from './pages/PageBuilder';
import Preview from './pages/Preview';

function App() {
  return (
    <Router>
      <div className="App">
        <header className="App-header">
          <h1>Vexel Builder</h1>
          <p>Visual Application Builder</p>
        </header>

        <main>
          <Routes>
            {/* Dashboard */}
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />

            {/* Application Builder */}
            <Route path="/app/new" element={<ApplicationBuilder appId={null} />} />
            <Route path="/app/:appId" element={<ApplicationBuilder />} />
            <Route path="/app/:appId/builder" element={<ApplicationBuilder />} />

            {/* Page Builder */}
            <Route path="/app/:appId/page/new" element={<PageBuilder pageId={null} />} />
            <Route path="/app/:appId/page/:pageId" element={<PageBuilder />} />
            <Route path="/app/:appId/page/:pageId/builder" element={<PageBuilder />} />

            {/* Preview */}
            <Route path="/app/:appId/page/:pageId/preview" element={<Preview />} />

            {/* Redirects */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;