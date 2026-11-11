"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "signup" | "forgot" | "reset">("login");
  const [resetToken, setResetToken] = useState("");
  
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("reset_token");
    if (token) {
      setResetToken(token);
      setMode("reset");
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setMessage("");

    if ((mode === "signup" || mode === "reset") && password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      if (mode === "signup") {
        const response = await fetch(`http://localhost:8001/api/auth/register`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password, full_name: fullName }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Registration failed");
        setMessage(data.message);
        setMode("login");
        setPassword("");
        setConfirmPassword("");
      } else if (mode === "login") {
        const response = await fetch(`http://localhost:8001/api/auth/login`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Login failed");
        localStorage.setItem("access_token", data.access_token);
        router.push("/");
      } else if (mode === "forgot") {
        const response = await fetch(`http://localhost:8001/api/auth/forgot-password`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Failed to send reset link");
        setMessage(data.message);
        setMode("login");
      } else if (mode === "reset") {
        const response = await fetch(`http://localhost:8001/api/auth/reset-password`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token: resetToken, new_password: password }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Failed to reset password");
        setMessage(data.message);
        setMode("login");
        setPassword("");
        setConfirmPassword("");
        router.replace("/login");
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrapper">
      <style>{`
        .auth-wrapper { min-height: 100vh; width: 100%; background: #0F1115; display: flex; align-items: center; justify-content: center; padding: 24px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; box-sizing: border-box; }
        .auth-card { width: 100%; max-width: 420px; background: #1A1D24; border: 1px solid #2D313A; border-radius: 16px; box-shadow: 0 20px 40px rgba(0,0,0,0.4); padding: 40px; box-sizing: border-box; }
        .auth-header { margin-bottom: 32px; }
        .auth-title { font-size: 24px; font-weight: 700; color: #FFFFFF; margin: 0 0 8px 0; letter-spacing: -0.5px; }
        .auth-subtitle { font-size: 14px; color: #9CA3AF; margin: 0; }
        .auth-alert-error { background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); color: #EF4444; font-size: 13px; padding: 12px; border-radius: 8px; margin-bottom: 24px; }
        .auth-alert-success { background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); color: #10B981; font-size: 13px; padding: 12px; border-radius: 8px; margin-bottom: 24px; }
        .auth-group { margin-bottom: 20px; }
        .auth-label-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .auth-label { font-size: 13px; font-weight: 600; color: #D1D5DB; }
        .auth-forgot { font-size: 12px; color: #3B82F6; text-decoration: none; background: none; border: none; cursor: pointer; padding: 0; }
        .auth-forgot:hover { text-decoration: underline; }
        .auth-input { width: 100%; background: #0B0C0F; border: 1px solid #2D313A; color: #FFFFFF; font-size: 14px; padding: 12px 16px; border-radius: 8px; outline: none; transition: border-color 0.2s; box-sizing: border-box; }
        .auth-input:focus { border-color: #3B82F6; }
        .auth-btn { width: 100%; background: #3B82F6; color: #FFFFFF; border: none; padding: 12px; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; margin-top: 8px; transition: 0.2s; }
        .auth-btn:disabled { opacity: 0.7; cursor: not-allowed; }
        .auth-footer { margin-top: 32px; text-align: center; font-size: 13px; color: #9CA3AF; }
        .auth-footer-link { background: none; border: none; color: #FFFFFF; font-weight: 600; cursor: pointer; margin-left: 6px; }
      `}</style>
      <div className="auth-card">
        <div className="auth-header">
          <h1 className="auth-title">
            {mode === "signup" ? "Create an account" : 
             mode === "forgot" ? "Reset Password" : 
             mode === "reset" ? "New Password" : "Welcome back"}
          </h1>
          <p className="auth-subtitle">
            {mode === "signup" ? "Sign up to start tailoring your resume." : 
             mode === "forgot" ? "We'll send you a secure reset link." :
             mode === "reset" ? "Enter your new credentials below." : "Log in to your dashboard."}
          </p>
        </div>
        
        {error && <div className="auth-alert-error">{error}</div>}
        {message && <div className="auth-alert-success">{message}</div>}
        
        <form onSubmit={handleSubmit} suppressHydrationWarning>
          {mode === "signup" && (
            <div className="auth-group">
              <div className="auth-label-row"><label className="auth-label">Full Name</label></div>
              <input type="text" required value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Jhone williams" className="auth-input" suppressHydrationWarning />
            </div>
          )}
          
          {(mode === "login" || mode === "signup" || mode === "forgot") && (
            <div className="auth-group">
              <div className="auth-label-row"><label className="auth-label">Email address</label></div>
              <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@university.edu" className="auth-input" suppressHydrationWarning />
            </div>
          )}
          
          {(mode === "login" || mode === "signup" || mode === "reset") && (
            <div className="auth-group">
              <div className="auth-label-row">
                <label className="auth-label">{mode === "reset" ? "New Password" : "Password"}</label>
                {mode === "login" && (
                  <button type="button" onClick={() => { setMode("forgot"); setError(""); setMessage(""); }} className="auth-forgot" suppressHydrationWarning>Forgot password?</button>
                )}
              </div>
              <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" className="auth-input" suppressHydrationWarning />
            </div>
          )}
          
          {(mode === "signup" || mode === "reset") && (
            <div className="auth-group">
              <div className="auth-label-row"><label className="auth-label">Confirm Password</label></div>
              <input type="password" required value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder="••••••••" className="auth-input" suppressHydrationWarning />
            </div>
          )}
          
          <button type="submit" disabled={loading} className="auth-btn" suppressHydrationWarning>
            {loading ? "Processing..." : 
             mode === "signup" ? "Sign up" : 
             mode === "forgot" ? "Send Reset Link" :
             mode === "reset" ? "Update Password" : "Log in"}
          </button>
        </form>
        
        {(mode === "login" || mode === "signup" || mode === "forgot") && (
          <div className="auth-footer">
            {mode === "signup" ? "Already have an account?" : "Don't have an account?"}
            <button type="button" className="auth-footer-link" onClick={() => { setMode(mode === "signup" ? "login" : "signup"); setError(""); setMessage(""); }} suppressHydrationWarning>
              {mode === "signup" || mode === "forgot" ? "Log in" : "Sign up"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
