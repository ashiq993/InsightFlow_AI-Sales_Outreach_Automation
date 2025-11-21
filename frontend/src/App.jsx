import React from 'react';
import './App.css';
import Header from './components/Header';
import Hero from './components/Hero';
import DataTemplateGuide from './components/DataTemplateGuide';
import FileUploader from './components/FileUploader';
import ThemeToggle from './components/ThemeToggle';

/**
 * Root application component that renders the main layout and primary UI sections.
 * @returns {JSX.Element} The app's top-level React element containing the header (with theme toggle), main content (hero, data template guide, file uploader), and footer.
 */
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