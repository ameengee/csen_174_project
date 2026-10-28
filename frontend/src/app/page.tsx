"use client";

import Image from "next/image";
import { useState, type SubmitEvent } from "react";
import styles from "./page.module.css";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";
const MAX_QUESTIONS = 3;
const JOBS_SHOWN = 10; // per role, before "Show all"

// The parts of the backend's ProfileAnalysis response this page uses.
type JobTarget = { name: string; why_it_fits: string; example_titles: string[] };
type Analysis = {
  profile: { career_stage: string };
  job_targets: JobTarget[];
  preferences: { locations: string[]; open_to_remote: boolean | null; notes: string[] };
  open_questions: string[];
};
type Role = { name: string; why?: string; exampleTitles: string[]; source: "suggested" | "added" };
type Level = "internship" | "entry_level" | "mid_level" | "senior";

// The backend's JobSearchResponse.
type JobResult = {
  company: string;
  title: string;
  location: string;
  url: string;
  posted: string | null;
  location_match: boolean;
};
type RoleResults = { role: string; jobs: JobResult[] };

type Step = "upload" | "analyzing" | "questions" | "roles" | "searching" | "results";

const STEP_LABELS = ["Upload", "Questions", "Roles", "Jobs"];
const STEP_INDEX: Record<Step, number> = {
  upload: 0,
  analyzing: 0,
  questions: 1,
  roles: 2,
  searching: 3,
  results: 3,
};

const LEVELS: { value: Level; label: string }[] = [
  { value: "internship", label: "Internship" },
  { value: "entry_level", label: "Entry level / new grad" },
  { value: "mid_level", label: "Mid level" },
  { value: "senior", label: "Senior" },
];

const LEVEL_FOR_STAGE: Record<string, Level> = {
  student: "internship",
  entry_level: "entry_level",
  mid_level: "mid_level",
  senior: "senior",
  executive: "senior",
};

function formatDate(iso: string | null) {
  if (!iso) return null;
  return new Date(`${iso}T00:00:00`).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

export default function Home() {
  const [step, setStep] = useState<Step>("upload");
  const [error, setError] = useState("");

  // upload
  const [file, setFile] = useState<File | null>(null);
  const [notes, setNotes] = useState("");

  // results of the analysis, then what the user does with them
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [questions, setQuestions] = useState<string[]>([]);
  const [answers, setAnswers] = useState<string[]>([]);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [roles, setRoles] = useState<Role[]>([]);
  const [newRole, setNewRole] = useState("");
  const [level, setLevel] = useState<Level>("internship");

  // job search
  const [results, setResults] = useState<RoleResults[]>([]);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  async function handleUpload(e: SubmitEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!file) return;

    const body = new FormData();
    body.append("file", file);
    if (notes.trim()) body.append("notes", notes);

    setError("");
    setStep("analyzing");
    try {
      const res = await fetch(`${API_URL}/profile/analyze`, { method: "POST", body });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? `Request failed (${res.status})`);

      const result = data as Analysis;
      const qs = result.open_questions.slice(0, MAX_QUESTIONS);
      setAnalysis(result);
      setQuestions(qs);
      setAnswers(qs.map(() => ""));
      setQuestionIndex(0);
      setRoles(
        result.job_targets.map((t) => ({
          name: t.name,
          why: t.why_it_fits,
          exampleTitles: t.example_titles,
          source: "suggested",
        })),
      );
      setLevel(LEVEL_FOR_STAGE[result.profile.career_stage] ?? "entry_level");
      setStep(qs.length > 0 ? "questions" : "roles");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setStep("upload");
    }
  }

  function nextQuestion() {
    if (questionIndex + 1 < questions.length) setQuestionIndex(questionIndex + 1);
    else setStep("roles");
  }

  function addRole(e: SubmitEvent<HTMLFormElement>) {
    e.preventDefault();
    const name = newRole.trim();
    if (!name) return;
    if (!roles.some((r) => r.name.toLowerCase() === name.toLowerCase())) {
      setRoles([...roles, { name, exampleTitles: [], source: "added" }]);
    }
    setNewRole("");
  }

  // Free-text preferences for the job matcher: their answers plus what the profile said.
  function searchContext() {
    const lines = questions
      .map((q, i) => (answers[i].trim() ? `Q: ${q}\nA: ${answers[i].trim()}` : ""))
      .filter(Boolean);
    const prefs = analysis?.preferences;
    if (prefs?.locations.length) lines.push(`Preferred locations: ${prefs.locations.join(", ")}`);
    if (prefs?.open_to_remote != null) lines.push(`Open to remote: ${prefs.open_to_remote}`);
    if (notes.trim()) lines.push(`Notes: ${notes.trim()}`);
    return lines.join("\n");
  }

  async function searchJobs() {
    setError("");
    setStep("searching");
    try {
      const res = await fetch(`${API_URL}/jobs/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          level,
          context: searchContext(),
          roles: roles.map((r) => ({ name: r.name, example_titles: r.exampleTitles })),
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? `Request failed (${res.status})`);
      setResults(data.results as RoleResults[]);
      setExpanded({});
      setStep("results");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setStep("roles");
    }
  }

  function startOver() {
    setStep("upload");
    setFile(null);
    setNotes("");
    setAnalysis(null);
    setResults([]);
    setError("");
  }

  const current = STEP_INDEX[step];

  return (
    <div className={styles.page}>
      <div className={styles.shell}>
        <ol className={styles.steps} aria-label="Progress">
          {STEP_LABELS.map((label, i) => (
            <li
              key={label}
              className={`${styles.step} ${i === current ? styles.stepActive : ""} ${
                i < current ? styles.stepDone : ""
              }`}
              aria-current={i === current ? "step" : undefined}
            >
              {label}
            </li>
          ))}
        </ol>

        <main className={styles.card}>
          {step === "upload" && (
            <>
              <h1 className={styles.title}>Upload your LinkedIn profile</h1>
              <p className={styles.subtitle}>
                We&apos;ll read it, ask a few quick questions, and suggest the kinds of roles to
                look for.
              </p>

              <ol className={styles.instructions}>
                <li>Open LinkedIn and go to your profile (click your photo, then View Profile).</li>
                <li>
                  Under your name, click <b>Resources</b>.
                </li>
                <li>
                  Click <b>Save to PDF</b>. LinkedIn downloads a file named <code>Profile.pdf</code>.
                </li>
              </ol>
              <Image
                className={styles.screenshot}
                src="/linkedin-save-to-pdf.png"
                alt="LinkedIn profile with the Resources menu open, showing Save to PDF"
                width={1144}
                height={314}
                priority
              />

              <form onSubmit={handleUpload}>
                <div className={styles.field}>
                  Profile PDF
                  <label className={styles.dropzone}>
                    <input
                      type="file"
                      accept=".pdf,application/pdf"
                      onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                    />
                    {file ? (
                      <span className={styles.dropzoneFile}>{file.name}</span>
                    ) : (
                      <span>Click to choose your Profile.pdf</span>
                    )}
                  </label>
                </div>
                <label className={styles.field}>
                  Anything else? <span className={styles.hint}>Optional</span>
                  <textarea
                    className={styles.textarea}
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Things missing from LinkedIn, where you want to work, roles to avoid…"
                  />
                </label>
                {error && <p className={styles.error}>{error}</p>}
                <button
                  type="submit"
                  className={`${styles.button} ${styles.buttonWide}`}
                  disabled={!file}
                >
                  Continue
                </button>
              </form>
            </>
          )}

          {step === "analyzing" && (
            <div className={styles.loading} role="status">
              <div className={styles.spinner} />
              <h1 className={styles.title}>Reading your profile…</h1>
              <p className={styles.subtitle}>This usually takes under a minute.</p>
            </div>
          )}

          {step === "questions" && (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                nextQuestion();
              }}
            >
              <p className={styles.eyebrow}>
                Question {questionIndex + 1} of {questions.length}
              </p>
              <h1 className={styles.question}>{questions[questionIndex]}</h1>
              <textarea
                key={questionIndex}
                className={styles.textarea}
                value={answers[questionIndex]}
                onChange={(e) =>
                  setAnswers(answers.map((a, i) => (i === questionIndex ? e.target.value : a)))
                }
                autoFocus
                aria-label="Your answer"
              />
              <div className={`${styles.actions} ${styles.actionsSplit}`} style={{ marginTop: 20 }}>
                <button
                  type="button"
                  className={styles.buttonGhost}
                  onClick={() =>
                    questionIndex > 0 ? setQuestionIndex(questionIndex - 1) : startOver()
                  }
                >
                  Back
                </button>
                <div className={styles.actions}>
                  <button type="button" className={styles.buttonGhost} onClick={nextQuestion}>
                    Skip
                  </button>
                  <button type="submit" className={styles.button}>
                    Next
                  </button>
                </div>
              </div>
            </form>
          )}

          {step === "roles" && (
            <>
              <h1 className={styles.title}>Roles to look for</h1>
              <p className={styles.subtitle}>
                Based on your profile. Remove any you don&apos;t want and add your own.
              </p>

              <label className={styles.field}>
                Level
                <select
                  className={styles.input}
                  value={level}
                  onChange={(e) => setLevel(e.target.value as Level)}
                >
                  {LEVELS.map((l) => (
                    <option key={l.value} value={l.value}>
                      {l.label}
                    </option>
                  ))}
                </select>
              </label>

              {roles.length === 0 ? (
                <p className={styles.empty}>No roles yet. Add at least one below.</p>
              ) : (
                <ul className={styles.roles}>
                  {roles.map((role) => (
                    <li key={role.name} className={styles.role}>
                      <div className={styles.roleBody}>
                        <div className={styles.roleName}>
                          {role.name}
                          {role.source === "added" && <span className={styles.roleTag}>Added</span>}
                        </div>
                        {role.why && <div className={styles.roleWhy}>{role.why}</div>}
                      </div>
                      <button
                        type="button"
                        className={styles.remove}
                        onClick={() => setRoles(roles.filter((r) => r !== role))}
                        aria-label={`Remove ${role.name}`}
                      >
                        ×
                      </button>
                    </li>
                  ))}
                </ul>
              )}

              <form className={styles.addRow} onSubmit={addRole}>
                <input
                  className={styles.input}
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value)}
                  placeholder="Add a role, e.g. Data Engineering Intern"
                  aria-label="New role"
                />
                <button type="submit" className={styles.buttonGhost} disabled={!newRole.trim()}>
                  Add
                </button>
              </form>

              {error && <p className={styles.error}>{error}</p>}
              <div className={`${styles.actions} ${styles.actionsSplit}`}>
                <button
                  type="button"
                  className={styles.buttonGhost}
                  onClick={() => (questions.length > 0 ? setStep("questions") : startOver())}
                >
                  Back
                </button>
                <button
                  type="button"
                  className={styles.button}
                  disabled={roles.length === 0}
                  onClick={searchJobs}
                >
                  Find jobs
                </button>
              </div>
            </>
          )}

          {step === "searching" && (
            <div className={styles.loading} role="status">
              <div className={styles.spinner} />
              <h1 className={styles.title}>Finding jobs…</h1>
              <p className={styles.subtitle}>
                Matching thousands of postings to your roles. This takes about 20 seconds.
              </p>
            </div>
          )}

          {step === "results" && (
            <>
              <h1 className={styles.title}>Jobs for you</h1>
              <p className={styles.subtitle}>
                {LEVELS.find((l) => l.value === level)?.label} roles, grouped by what you&apos;re
                looking for. Jobs that match your location come first.
              </p>

              {results.map(({ role, jobs }) => {
                const shown = expanded[role] ? jobs : jobs.slice(0, JOBS_SHOWN);
                return (
                  <section key={role} className={styles.resultSection}>
                    <h2 className={styles.resultRole}>
                      {role} <span className={styles.resultCount}>{jobs.length}</span>
                    </h2>
                    {jobs.length === 0 ? (
                      <p className={styles.empty}>No open postings found for this role.</p>
                    ) : (
                      <ul className={styles.jobs}>
                        {shown.map((job) => (
                          <li key={job.url + job.location} className={styles.job}>
                            <a
                              className={styles.jobTitle}
                              href={job.url}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              {job.title}
                            </a>
                            <div className={styles.jobMeta}>
                              <span className={styles.jobCompany}>{job.company}</span>
                              <span>{job.location}</span>
                              {job.posted && <span>{formatDate(job.posted)}</span>}
                              {job.location_match && (
                                <span className={styles.roleTag}>Location match</span>
                              )}
                            </div>
                          </li>
                        ))}
                      </ul>
                    )}
                    {jobs.length > JOBS_SHOWN && (
                      <button
                        type="button"
                        className={styles.linkButton}
                        onClick={() => setExpanded({ ...expanded, [role]: !expanded[role] })}
                      >
                        {expanded[role] ? "Show fewer" : `Show all ${jobs.length}`}
                      </button>
                    )}
                  </section>
                );
              })}

              <div className={`${styles.actions} ${styles.actionsSplit}`}>
                <button type="button" className={styles.buttonGhost} onClick={() => setStep("roles")}>
                  Back
                </button>
                <button type="button" className={styles.button} onClick={startOver}>
                  Start over
                </button>
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  );
}
