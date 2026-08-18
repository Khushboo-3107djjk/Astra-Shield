import React, { useState } from 'react';

/**
 * Analyze.jsx - Main analysis dashboard
 * Person 3's primary component
 * 
 * Flow: Upload → Detect → Compare → Impact → Risk → Response
 */

function Analyze() {
  const [step, setStep] = useState('upload'); // upload, detecting, detect, compare, impact, risk, response
  const [selectedDisaster, setSelectedDisaster] = useState('flood');
  const [beforeImage, setBeforeImage] = useState(null);
  const [afterImage, setAfterImage] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const disasters = ['Flood', 'Wildfire', 'Cyclone', 'Landslide', 'Earthquake', 'Drought'];

  const handleAnalyze = async () => {
    setLoading(true);
    setStep('detecting');

    try {
      // TODO: Call backend API
      // const response = await fetch('/api/analyze', {
      //   method: 'POST',
      //   body: formData
      // });
      // const result = await response.json();
      // setAnalysisResult(result);
      
      setStep('detect');
      setTimeout(() => setStep('compare'), 2000);
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white p-8">
      <h1 className="text-4xl font-bold mb-8">🛰️ ASTRA-SHIELD Analysis</h1>

      {step === 'upload' && (
        <div className="max-w-2xl mx-auto">
          <h2 className="text-2xl font-semibold mb-6">Step 1: Select Disaster Type</h2>
          
          <div className="grid grid-cols-2 gap-4 mb-8">
            {disasters.map(disaster => (
              <button
                key={disaster}
                onClick={() => setSelectedDisaster(disaster.toLowerCase())}
                className={`p-4 rounded-lg font-semibold transition ${
                  selectedDisaster === disaster.toLowerCase()
                    ? 'bg-blue-600'
                    : 'bg-slate-700 hover:bg-slate-600'
                }`}
              >
                {disaster}
              </button>
            ))}
          </div>

          <h2 className="text-2xl font-semibold mb-6">Step 2: Upload Satellite Images</h2>
          
          <div className="grid grid-cols-2 gap-6 mb-8">
            <div className="border-2 border-dashed border-blue-400 p-8 rounded-lg text-center">
              <p className="mb-4">📷 Before Image</p>
              <input type="file" accept="image/*" onChange={(e) => setBeforeImage(e.target.files[0])} />
            </div>
            
            <div className="border-2 border-dashed border-blue-400 p-8 rounded-lg text-center">
              <p className="mb-4">📷 After Image</p>
              <input type="file" accept="image/*" onChange={(e) => setAfterImage(e.target.files[0])} />
            </div>
          </div>

          <button
            onClick={handleAnalyze}
            disabled={loading || !beforeImage || !afterImage}
            className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-600 px-6 py-3 rounded-lg font-bold text-lg"
          >
            {loading ? 'Analyzing...' : '[ ANALYZE ]'}
          </button>
        </div>
      )}

      {step === 'detecting' && (
        <div className="text-center">
          <p className="text-2xl mb-4">🤖 AI is analyzing...</p>
          <div className="animate-spin text-4xl">⚙️</div>
        </div>
      )}

      {step === 'detect' && (
        <div>
          {/* TODO: AI Detection component */}
          <p>AI Detection Results</p>
          <button onClick={() => setStep('compare')} className="mt-4 bg-blue-600 px-4 py-2 rounded">
            Next: Before/After Comparison →
          </button>
        </div>
      )}

      {step === 'compare' && (
        <div>
          {/* TODO: Before/After slider component - THIS IS YOUR WOW FACTOR! */}
          <p className="text-2xl font-bold text-yellow-400">⭐ Disaster Evolution - YOUR WOW MOMENT!</p>
          <p>Build the slider/swipe comparison here</p>
          <button onClick={() => setStep('impact')} className="mt-4 bg-blue-600 px-4 py-2 rounded">
            Next: Impact Analysis →
          </button>
        </div>
      )}

      {step === 'impact' && (
        <div>
          {/* TODO: Impact statistics & map */}
          <p>Impact Analysis</p>
          <button onClick={() => setStep('risk')} className="mt-4 bg-blue-600 px-4 py-2 rounded">
            Next: Risk Zones →
          </button>
        </div>
      )}

      {step === 'risk' && (
        <div>
          {/* TODO: Risk zone visualization */}
          <p>Risk Zones</p>
          <button onClick={() => setStep('response')} className="mt-4 bg-blue-600 px-4 py-2 rounded">
            Next: Emergency Response →
          </button>
        </div>
      )}

      {step === 'response' && (
        <div>
          {/* TODO: Emergency alerts & recommendations */}
          <p>Emergency Response</p>
          <button onClick={() => setStep('upload')} className="mt-4 bg-blue-600 px-4 py-2 rounded">
            Start New Analysis
          </button>
        </div>
      )}
    </div>
  );
}

export default Analyze;
