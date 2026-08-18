import React, { useState, useRef } from 'react';

/**
 * Analyze.jsx - Satellite image comparison and analysis screen
 */
function Analyze({ onBackToHome }) {
  const [beforeFile, setBeforeFile] = useState(null);
  const [afterFile, setAfterFile] = useState(null);
  const [beforePreview, setBeforePreview] = useState(null);
  const [afterPreview, setAfterPreview] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzed, setIsAnalyzed] = useState(false);

  const beforeInputRef = useRef(null);
  const afterInputRef = useRef(null);

  const handleBeforeChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (beforePreview) URL.revokeObjectURL(beforePreview);
      setBeforeFile(file);
      setBeforePreview(URL.createObjectURL(file));
    }
  };

  const handleAfterChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (afterPreview) URL.revokeObjectURL(afterPreview);
      setAfterFile(file);
      setAfterPreview(URL.createObjectURL(file));
    }
  };

  const handleRunAnalysis = () => {
    if (!beforePreview || !afterPreview) return;
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      setIsAnalyzed(true);
    }, 1500); // Brief 1.5s loading simulation
  };

  const handleReset = () => {
    if (beforePreview) URL.revokeObjectURL(beforePreview);
    if (afterPreview) URL.revokeObjectURL(afterPreview);
    setBeforeFile(null);
    setAfterFile(null);
    setBeforePreview(null);
    setAfterPreview(null);
    setIsAnalyzed(false);
  };

  if (isLoading) {
    return (
      <div className="analysis">
        <div className="loading-container">
          <div className="spinner"></div>
          <div className="loading-text">Running AI Analysis...</div>
        </div>
      </div>
    );
  }

  if (isAnalyzed) {
    return (
      <div className="analysis">
        <div className="results-container">
          <div className="results-header">
            <div className="results-status">ANALYSIS READY</div>
            <p className="results-desc">Change detection analysis completed successfully using selected imagery.</p>
          </div>
          <div className="results-grid">
            <div className="results-card">
              <h3>Before Image</h3>
              <div className="results-image-wrapper">
                <img src={beforePreview} alt="Before Event" className="results-image" />
              </div>
            </div>
            <div className="results-card">
              <h3>After Image</h3>
              <div className="results-image-wrapper">
                <img src={afterPreview} alt="After Event" className="results-image" />
              </div>
            </div>
          </div>
          <div className="results-actions">
            <button className="primary-button" onClick={handleReset}>Start New Analysis</button>
            <button className="secondary-button" onClick={onBackToHome}>Back to Home</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="analysis">
      <div className="analysis-header">
        <button className="secondary-button" style={{ marginBottom: '1.5rem' }} onClick={onBackToHome}>
          Back to Home
        </button>
        <h1>Begin Analysis</h1>
        <p>Upload satellite imagery to compare conditions before and after a disaster.</p>
      </div>

      <div className="upload-grid">
        <div className="upload-section">
          <h3>Before Event</h3>
          <input
            type="file"
            accept="image/*"
            ref={beforeInputRef}
            onChange={handleBeforeChange}
            style={{ display: 'none' }}
          />
          {beforePreview ? (
            <div className="image-preview-container">
              <img src={beforePreview} alt="Before Event Preview" className="image-preview" />
              <div className="image-meta">
                <span className="image-filename">{beforeFile ? beforeFile.name : ''}</span>
                <button className="secondary-button" onClick={() => beforeInputRef.current.click()}>
                  Change Image
                </button>
              </div>
            </div>
          ) : (
            <div className="upload-box" onClick={() => beforeInputRef.current.click()}>
              <span>Select Image</span>
            </div>
          )}
        </div>

        <div className="upload-section">
          <h3>After Event</h3>
          <input
            type="file"
            accept="image/*"
            ref={afterInputRef}
            onChange={handleAfterChange}
            style={{ display: 'none' }}
          />
          {afterPreview ? (
            <div className="image-preview-container">
              <img src={afterPreview} alt="After Event Preview" className="image-preview" />
              <div className="image-meta">
                <span className="image-filename">{afterFile ? afterFile.name : ''}</span>
                <button className="secondary-button" onClick={() => afterInputRef.current.click()}>
                  Change Image
                </button>
              </div>
            </div>
          ) : (
            <div className="upload-box" onClick={() => afterInputRef.current.click()}>
              <span>Select Image</span>
            </div>
          )}
        </div>
      </div>

      <div className="action-bar">
        <button
          className="primary-button"
          disabled={!beforePreview || !afterPreview}
          onClick={handleRunAnalysis}
        >
          Run Analysis
        </button>
      </div>
    </div>
  );
}

export default Analyze;
