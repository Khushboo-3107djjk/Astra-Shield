import React from 'react';

/**
 * MissionControl.jsx - Home/Landing page
 * Displays project intro and starts analysis flow
 */
function MissionControl({ onStartAnalysis }) {
  return (
    <div className="landing">
      <div className="hero">
        <p className="subtitle">AI-powered satellite disaster intelligence</p>
        <h1>ASTRA-<span className="accent">SHIELD</span></h1>
        <p className="description">
          Use satellite imagery and AI to detect disaster impact, assess affected infrastructure, identify high-risk zones, and support emergency response decisions.
        </p>
        <button className="primary-button" onClick={onStartAnalysis}>
          Begin Analysis
        </button>
      </div>
    </div>
  );
}

export default MissionControl;
