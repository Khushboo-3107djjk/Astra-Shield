import React, { useState } from 'react';
import MissionControl from './pages/MissionControl';
import Analyze from './pages/Analyze';

function App() {
  const [page, setPage] = useState('landing'); // 'landing' or 'analysis'

  return (
    <div className="app">
      {page === 'landing' ? (
        <MissionControl onStartAnalysis={() => setPage('analysis')} />
      ) : (
        <Analyze onBackToHome={() => setPage('landing')} />
      )}
    </div>
  );
}

export default App;
