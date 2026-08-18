/**
 * API Service - Frontend API calls to backend
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

export const analyzeImage = async (formData) => {
  const response = await fetch(`${API_BASE_URL}/analyze`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) throw new Error('Analysis failed');
  return response.json();
};

export const getAnalysisResult = async (id) => {
  const response = await fetch(`${API_BASE_URL}/results/${id}`);
  if (!response.ok) throw new Error('Failed to fetch results');
  return response.json();
};

export const calculateImpact = async (disasterData) => {
  const response = await fetch(`${API_BASE_URL}/impact`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(disasterData),
  });
  if (!response.ok) throw new Error('Impact calculation failed');
  return response.json();
};

export const getRiskZones = async (disasterType) => {
  const response = await fetch(`${API_BASE_URL}/zones/${disasterType}`);
  if (!response.ok) throw new Error('Failed to fetch risk zones');
  return response.json();
};

export const getEmergencyAlert = async (disasterData) => {
  const response = await fetch(`${API_BASE_URL}/emergency-alert`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(disasterData),
  });
  if (!response.ok) throw new Error('Alert generation failed');
  return response.json();
};
