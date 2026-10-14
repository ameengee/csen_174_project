"use client";

import Image from "next/image";
import { useState, type SubmitEvent } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [notes, setNotes] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "error" | "done">("idle");
  const [result, setResult] = useState("");

  async function handleSubmit(e: SubmitEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!file) return;

    const body = new FormData();
    body.append("file", file);
    if (notes.trim()) body.append("notes", notes);

    setStatus("loading");
    setResult("");
    try {
      const res = await fetch(`${API_URL}/profile/analyze`, { method: "POST", body });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? `Request failed (${res.status})`);
      setResult(JSON.stringify(data, null, 2));
      setStatus("done");
    } catch (err) {
      setResult(err instanceof Error ? err.message : String(err));
      setStatus("error");
    }
  }

  return (
    <main style={{ maxWidth: 640, margin: "0 auto", padding: "40px 16px", lineHeight: 1.5 }}>
      <h1 style={{ marginBottom: 16 }}>Upload your LinkedIn profile</h1>

      <h2 style={{ fontSize: 18, marginTop: 24 }}>Option 1: Save your profile as a PDF (fastest)</h2>
      <ol style={{ paddingLeft: 20, margin: "8px 0 16px" }}>
        <li>Open LinkedIn and go to your profile (click your photo, then View Profile).</li>
        <li>
          Under your name, click <b>Resources</b>.
        </li>
        <li>
          Click <b>Save to PDF</b>. LinkedIn downloads a file named <code>Profile.pdf</code>.
        </li>
      </ol>
      <Image
        src="/linkedin-save-to-pdf.png"
        alt="LinkedIn profile with the Resources menu open, showing Save to PDF"
        width={1144}
        height={314}
        style={{ width: "100%", height: "auto", border: "1px solid #ccc", borderRadius: 8 }}
      />

      <h2 style={{ fontSize: 18, marginTop: 24 }}>Option 2: Download your LinkedIn data (most complete)</h2>
      <ol style={{ paddingLeft: 20, margin: "8px 0 16px" }}>
        <li>
          Click <b>Me</b> → <b>Settings &amp; Privacy</b> → <b>Data privacy</b> →{" "}
          <b>Get a copy of your data</b>.
        </li>
        <li>Choose the full archive, or select Profile, Positions, Education and Skills.</li>
        <li>LinkedIn emails you a link, usually within a day. Download the <code>.zip</code>.</li>
      </ol>

      <form onSubmit={handleSubmit} style={{ display: "grid", gap: 12, marginTop: 24 }}>
        <label>
          Profile PDF or data export .zip
          <br />
          <input
            type="file"
            accept=".pdf,.zip,application/pdf,application/zip"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            required
          />
        </label>
        <label>
          Anything else? (optional: things missing from LinkedIn, where you want to work, roles to avoid)
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={4}
            style={{ width: "100%", marginTop: 4, padding: 8, font: "inherit" }}
          />
        </label>
        <button
          type="submit"
          disabled={!file || status === "loading"}
          style={{ padding: "10px 16px", font: "inherit", cursor: "pointer" }}
        >
          {status === "loading" ? "Analyzing… (this can take a minute)" : "Submit"}
        </button>
      </form>

      {result && (
        <pre
          style={{
            marginTop: 24,
            padding: 12,
            whiteSpace: "pre-wrap",
            border: "1px solid #ccc",
            borderRadius: 8,
            color: status === "error" ? "#c00" : "inherit",
          }}
        >
          {result}
        </pre>
      )}
    </main>
  );
}
