import React from 'react';

/**
 * MissionControl.jsx - Home/Overview page
 * Shows project intro and launches analysis
 */

function MissionControl() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 text-white flex flex-col justify-center items-center">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-6xl font-bold mb-2">🛰️ ASTRA-SHIELD</h1>
        <p className="text-2xl text-blue-300 mb-4">AI-Powered Satellite Disaster Intelligence</p>
        <p className="text-xl text-gray-300">See. Understand. Respond.</p>
      </div>

      {/* Disaster Types */}
      <div className="mb-12">
        <p className="text-gray-300 mb-4">Supported Disasters:</p>
        <div className="flex gap-4 justify-center flex-wrap">
          {['🌊 Flood', '🔥 Wildfire', '🌀 Cyclone', '⛰️ Landslide', '🌍 Earthquake', '☀️ Drought'].map(d => (
            <span key={d} className="bg-slate-700 px-4 py-2 rounded-full">{d}</span>
          ))}
        </div>
      </div>

      {/* CTA Button */}
      <button className="bg-gradient-to-r from-blue-600 to-cyan-500 px-12 py-4 rounded-lg font-bold text-lg hover:shadow-lg hover:shadow-blue-500/50 transition transform hover:scale-105">
        [ Launch Analysis ]
      </button>

      {/* About */}
      <div className="mt-16 max-w-2xl text-center text-gray-400">
        <p>
          ASTRA-SHIELD uses cutting-edge AI and satellite imagery to detect, analyze, and respond to natural disasters in real-time.
        </p>
      </div>
    </div>
  );
}

export default MissionControl;
