import React from 'react';
import MainLayout from './components/MainLayout';
import { ThemeProvider } from './contexts/ThemeContext';
import './App.css';

function App() {
  return (
    <ThemeProvider>
      <div className="App h-screen">
        <MainLayout />
      </div>
    </ThemeProvider>
  );
}

export default App;