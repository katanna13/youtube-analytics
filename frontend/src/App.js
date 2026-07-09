import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Overview from './pages/Overview';
import BestTimes from './pages/BestTimes';
import MLPredictor from './pages/MLPredictor';
import AIInsights from './pages/AIInsights';
import ChannelAudit from './pages/ChannelAudit';
import './App.css';

const PAGES = {
  overview: Overview,
  bestTimes: BestTimes,
  mlPredictor: MLPredictor,
  aiInsights: AIInsights,
  channelAudit: ChannelAudit,
};

export default function App() {
  const [activePage, setActivePage] = useState('overview');
  const PageComponent = PAGES[activePage];

  return (
    <div className="app">
      <Sidebar activePage={activePage} onNavigate={setActivePage} />
      <main className="main-content">
        <PageComponent />
      </main>
    </div>
  );
}
