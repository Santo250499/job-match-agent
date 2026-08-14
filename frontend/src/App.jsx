import { useState } from "react";
import "./App.css";

const API_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

function getApiError(data, status) {
  if (typeof data?.detail === "string") {
    return data.detail;
  }

  if (Array.isArray(data?.detail)) {
    const messages = data.detail
      .map((item) => item?.msg)
      .filter(Boolean);

    if (messages.length > 0) {
      return messages.join(" ");
    }
  }

  return `The request failed with status ${status}.`;
}

function getScoreLabel(score) {
  if (score >= 80) {
    return "Strong Match";
  }

  if (score >= 60) {
    return "Moderate Match";
  }

  return "Needs Improvement";
}

function SkillGroup({ title, items, tone }) {
  return (
    <section className={`skill-panel ${tone}`}>
      <div className="section-heading">
        <h3>{title}</h3>
        <span className="count-badge">{items.length}</span>
      </div>

      {items.length === 0 ? (
        <p className="empty-message">
          No skills were identified in this category.
        </p>
      ) : (
        <div className="skill-list">
          {items.map((item, index) => (
            <article
              className="skill-item"
              key={`${item.skill}-${index}`}
            >
              <h4>{item.skill}</h4>

              <div className="skill-detail">
                <span>Evidence</span>
                <p>{item.evidence}</p>
              </div>

              <div className="skill-detail">
                <span>Recommendation</span>
                <p>{item.recommendation}</p>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function BulletSection({ title, items }) {
  if (!items || items.length === 0) {
    return null;
  }

  return (
    <section className="detail-panel">
      <h3>{title}</h3>

      <ul>
        {items.map((item, index) => (
          <li key={`${title}-${index}`}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

function App() {
  const [resumeText, setResumeText] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [australianContext, setAustralianContext] =
    useState(true);

  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();

    setError("");
    setResult(null);

    const cleanResume = resumeText.trim();
    const cleanJobDescription = jobDescription.trim();

    if (cleanResume.length < 50) {
      setError(
        "Your résumé must contain at least 50 characters."
      );
      return;
    }

    if (cleanJobDescription.length < 50) {
      setError(
        "The job description must contain at least 50 characters."
      );
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/analyse`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          resume_text: resumeText,
          job_description: jobDescription,
          australian_context: australianContext,
        }),
      });

      const data = await response
        .json()
        .catch(() => null);

      if (!response.ok) {
        throw new Error(
          getApiError(data, response.status)
        );
      }

      setResult(data);

      setTimeout(() => {
        document
          .getElementById("results")
          ?.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
      }, 100);
    } catch (requestError) {
      if (requestError instanceof TypeError) {
        setError(
          "Could not connect to the API. Make sure the FastAPI server is running on port 8000."
        );
      } else {
        setError(
          requestError.message ||
            "Something went wrong while analysing the job match."
        );
      }
    } finally {
      setLoading(false);
    }
  }

  function handleClear() {
    setResumeText("");
    setJobDescription("");
    setAustralianContext(true);
    setResult(null);
    setError("");
  }

  return (
    <main className="app">
      <section className="hero">
        <div className="hero-badge">
          Smart Resume Intelligence
        </div>

        <h1>AI Job Match Agent</h1>

        <p className="hero-text">
          Instantly compare your résumé with any job
          description and receive a professional AI-powered
          match analysis with strengths, skill gaps, and
          actionable next steps.
        </p>
      </section>

      <section className="analysis-card">
        <form
          className="analysis-form"
          onSubmit={handleSubmit}
        >
          <div className="input-grid">
            <div className="field">
              <label htmlFor="resume">
                Résumé
              </label>

              <textarea
                id="resume"
                value={resumeText}
                onChange={(event) =>
                  setResumeText(event.target.value)
                }
                placeholder="Paste your résumé here..."
                rows="14"
              />

              <div className="field-footer">
                <span>Minimum 50 characters</span>

                <span>
                  {resumeText.length} characters
                </span>
              </div>
            </div>

            <div className="field">
              <label htmlFor="job-description">
                Job Description
              </label>

              <textarea
                id="job-description"
                value={jobDescription}
                onChange={(event) =>
                  setJobDescription(event.target.value)
                }
                placeholder="Paste the job description here..."
                rows="14"
              />

              <div className="field-footer">
                <span>Minimum 50 characters</span>

                <span>
                  {jobDescription.length} characters
                </span>
              </div>
            </div>
          </div>

          <div className="form-actions">
            <label className="checkbox-row">
              <input
                type="checkbox"
                checked={australianContext}
                onChange={(event) =>
                  setAustralianContext(
                    event.target.checked
                  )
                }
              />

              <span>
                Include Australian employment market context
              </span>
            </label>

            <div className="button-group">
              <button
                type="button"
                className="secondary-button"
                onClick={handleClear}
                disabled={loading}
              >
                Clear
              </button>

              <button
                type="submit"
                className="analyse-button"
                disabled={loading}
              >
                {loading
                  ? "Analysing..."
                  : "Analyse Match"}
              </button>
            </div>
          </div>
        </form>
      </section>

      {error && (
        <div
          className="error-banner"
          role="alert"
        >
          <strong>Analysis failed</strong>
          <span>{error}</span>
        </div>
      )}

      {loading && (
        <section
          className="loading-card"
          aria-live="polite"
        >
          <div className="loading-spinner" />

          <div>
            <strong>Analysing your match</strong>
            <p>
              Comparing your résumé with the job
              requirements...
            </p>
          </div>
        </section>
      )}

      {result && (
        <section
          className="results"
          id="results"
        >
          <div className="results-header">
            <div
              className="score-circle"
              style={{
                "--score": `${result.overall_score * 3.6}deg`,
              }}
            >
              <div className="score-inner">
                <strong>
                  {result.overall_score}
                </strong>
                <span>/100</span>
              </div>
            </div>

            <div className="results-intro">
              <span className="result-label">
                {getScoreLabel(
                  result.overall_score
                )}
              </span>

              <h2>Your Job Match Analysis</h2>

              <p>{result.summary}</p>
            </div>
          </div>

          <section className="score-explanation">
            <span>How the score was calculated</span>
            <p>{result.score_explanation}</p>
          </section>

          <div className="skills-grid">
            <SkillGroup
              title="Matched Skills"
              items={result.matched_skills}
              tone="matched"
            />

            <SkillGroup
              title="Partial Skills"
              items={result.partial_skills}
              tone="partial"
            />

            <SkillGroup
              title="Missing Skills"
              items={result.missing_skills}
              tone="missing"
            />
          </div>

          <div className="details-grid">
            <BulletSection
              title="Recommended Actions"
              items={result.recommended_actions}
            />

            <BulletSection
              title="Information to Confirm"
              items={result.information_to_confirm}
            />

            <BulletSection
              title="Australian Market Notes"
              items={result.australian_market_notes}
            />
          </div>

          <div className="honesty-notice">
            <span>Responsible AI</span>

            <p>{result.honesty_statement}</p>
          </div>
        </section>
      )}
    </main>
  );
}

export default App;