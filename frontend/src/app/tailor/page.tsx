"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const router = useRouter();
  const [resume, setResume] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  // The Bouncer: Kick them back to login if they don't have a token
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.replace("/login");
    }
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    router.replace("/login");
  };

  const handleTailor = async () => {
    if (!resume.trim() || !jobDescription.trim()) {
      setError("Please paste both your master resume and the target job description.");
      return;
    }
    setError("");
    setLoading(true);
    setResult("");
    setCopied(false);

    try {
      const response = await fetch("http://localhost:8001/api/tailor/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume, job_description: jobDescription }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || "Failed to connect to the AI engine.");
      }

      setResult(data.tailored_text);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(result);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="dashboard-wrapper">
      <style>{`
        .dashboard-wrapper { min-height: 100vh; width: 100%; background: #0F1115; color: #FFFFFF; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        .nav-bar { display: flex; justify-content: space-between; align-items: center; padding: 20px 40px; background: #1A1D24; border-bottom: 1px solid #2D313A; }
        .logo { font-size: 20px; font-weight: 700; color: #FFFFFF; letter-spacing: -0.5px; }
        .logout-btn { background: transparent; border: 1px solid #374151; color: #9CA3AF; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 600; transition: 0.2s; }
        .logout-btn:hover { background: #374151; color: #FFF; }
        
        .main-container { max-width: 1200px; margin: 0 auto; padding: 40px 20px; display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
        @media (max-width: 768px) { .main-container { grid-template-columns: 1fr; } }
        
        .panel { background: #1A1D24; border: 1px solid #2D313A; border-radius: 12px; padding: 24px; display: flex; flex-direction: column; gap: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .panel-title { font-size: 18px; font-weight: 600; margin: 0; color: #F3F4F6; }
        
        .input-label { font-size: 13px; font-weight: 600; color: #9CA3AF; margin-bottom: 6px; display: block; }
        .text-area { width: 100%; height: 180px; background: #0B0C0F; border: 1px solid #2D313A; color: #E5E7EB; padding: 16px; border-radius: 8px; font-size: 14px; font-family: inherit; resize: none; outline: none; transition: border-color 0.2s; box-sizing: border-box; }
        .text-area:focus { border-color: #3B82F6; }
        
        .action-btn { background: #3B82F6; color: #FFF; border: none; padding: 14px; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; transition: 0.2s; display: flex; justify-content: center; align-items: center; gap: 8px; }
        .action-btn:hover { background: #2563EB; }
        .action-btn:disabled { opacity: 0.6; cursor: not-allowed; }
        
        .error-banner { background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); color: #EF4444; font-size: 13px; padding: 12px; border-radius: 8px; }
        
        .result-box { flex-grow: 1; background: #0B0C0F; border: 1px solid #2D313A; border-radius: 8px; padding: 20px; font-size: 15px; line-height: 1.6; color: #D1D5DB; white-space: pre-wrap; overflow-y: auto; min-height: 300px; }
        .empty-state { height: 100%; display: flex; align-items: center; justify-content: center; color: #4B5563; font-size: 14px; text-align: center; font-style: italic; }
        
        .copy-btn { background: #10B981; color: white; border: none; padding: 10px 16px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; transition: 0.2s; margin-top: auto; }
        .copy-btn:hover { background: #059669; }
      `}</style>

      <nav className="nav-bar">
        <div className="logo">AI Resume Tailor</div>
        <button onClick={handleLogout} className="logout-btn">Log out</button>
      </nav>

      <main className="main-container">
        {/* LEFT COLUMN: Inputs */}
        <div className="panel">
          <h2 className="panel-title">Your Details</h2>
          
          {error && <div className="error-banner">{error}</div>}

          <div>
            <label className="input-label">Master Resume (Raw Text)</label>
            <textarea 
              className="text-area" 
              placeholder="Paste your current resume experience here..."
              value={resume}
              onChange={(e) => setResume(e.target.value)}
            />
          </div>

          <div>
            <label className="input-label">Target Job Description</label>
            <textarea 
              className="text-area" 
              placeholder="Paste the job requirements and description here..."
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
            />
          </div>

          <button onClick={handleTailor} disabled={loading} className="action-btn">
            {loading ? (
              "Analyzing match & tailoring..."
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                Generate Optimized Bullets
              </>
            )}
          </button>
        </div>

        {/* RIGHT COLUMN: AI Results */}
        <div className="panel">
          <h2 className="panel-title">Tailored Output</h2>
          <div className="result-box">
            {loading ? (
              <div className="empty-state">Gemini 1.5 is rewriting your experience...</div>
            ) : result ? (
              result
            ) : (
              <div className="empty-state">Your optimized resume bullets will appear here.</div>
            )}
          </div>
          
          {result && !loading && (
            <button onClick={copyToClipboard} className="copy-btn">
              {copied ? "Copied to Clipboard!" : "Copy Output"}
            </button>
          )}
        </div>
      </main>
    </div>
  );
}
