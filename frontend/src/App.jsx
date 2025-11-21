import React from 'react';
import './App.css';
import Header from './components/Header';
import Hero from './components/Hero';
import DataTemplateGuide from './components/DataTemplateGuide';
import FileUploader from './components/FileUploader';
import ThemeToggle from './components/ThemeToggle';

function App() {
  return (
    <div className="app-container">
      <Header>
        <ThemeToggle />
      </Header>
      <main className="container">
        <Hero />
        <DataTemplateGuide />
        <FileUploader />
      </main>

      <footer style={{ textAlign: 'center', padding: '40px 0', color: '#64748b', fontSize: '0.9rem' }}>
        <p>© 2025 InsightFlow AI. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default App;
