import React from 'react';
import MissionControl from './pages/MissionControl';
import Analyze from './pages/Analyze';

/**
 * App.jsx - Main React app entry point
 * TODO: Add React Router for page navigation
 */

function App() {
  return (
    <div className="App">
      <MissionControl />
      {/* <Analyze /> */}
    </div>
  );
}

export default App;
