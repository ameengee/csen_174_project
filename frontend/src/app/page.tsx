"use client";

import Image from "next/image";
import { useState, type SubmitEvent } from "react";
import styles from "./page.module.css";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";
const MAX_QUESTIONS = 3;

// The parts of the backend's ProfileAnalysis response this page uses; the rest passes through.
type JobTarget = { name: string; why_it_fits: string };
type Analysis = {
  job_targets: JobTarget[];
  open_questions: string[];
  [key: string]: unknown;
};
type Role = { name: string; why?: string; source: "suggested" | "added" };
type Step = "upload" | "analyzing" | "questions" | "roles" | "done";

const STEP_LABELS = ["Upload", "Questions", "Roles", "Done"];
const STEP_INDEX: Record<Step, number> = {
  upload: 0,
  analyzing: 0,
  questions: 1,
  roles: 2,
  done: 3,
};

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
        result.job_targets.map((t) => ({ name: t.name, why: t.why_it_fits, source: "suggested" })),
      );
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
      setRoles([...roles, { name, source: "added" }]);
    }
    setNewRole("");
  }

  function startOver() {
    setStep("upload");
    setFile(null);
    setNotes("");
    setAnalysis(null);
    setError("");
  }

  // What gets handed to the next backend step (job search) once it exists.
  const finalPayload = analysis && {
    ...analysis,
    // Drop suggested targets the user removed, so job_targets and job_roles agree.
    job_targets: analysis.job_targets.filter((t) => roles.some((r) => r.name === t.name)),
    answers: questions.map((q, i) => ({ question: q, answer: answers[i].trim() || null })),
    job_roles: roles.map(({ name, source }) => ({ name, source })),
  };

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
                  onClick={() => setStep("done")}
                >
                  Submit
                </button>
              </div>
            </>
          )}

          {step === "done" && (
            <>
              <h1 className={styles.title}>You&apos;re all set</h1>
              <p className={styles.subtitle}>
                This is what we&apos;ll use to find jobs for you. Job search comes next.
              </p>
              <pre className={styles.json}>{JSON.stringify(finalPayload, null, 2)}</pre>
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
