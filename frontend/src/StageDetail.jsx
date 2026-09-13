function ScoreRow({ label, value }) {
  return (
    <div className="score-row">
      <span className="score-row-label">{label}</span>
      <span className="score-row-value">{value ?? "—"}</span>
    </div>
  );
}

function CandidateCard({ index, email, evaluation, isBest }) {
  return (
    <div className={`candidate ${isBest ? "candidate--best" : ""}`}>
      <div className="candidate-head">
        <span className="candidate-title">Version {index + 1}</span>
        {isBest && <span className="candidate-badge">Selected</span>}
      </div>
      <pre className="candidate-body">{email}</pre>
      {evaluation && (
        <div className="score-grid">
          <ScoreRow label="Clarity" value={evaluation.clarity} />
          <ScoreRow label="CTA" value={evaluation.cta} />
          <ScoreRow label="Tone" value={evaluation.tone} />
          <ScoreRow label="Overall" value={evaluation.overall_score} />
        </div>
      )}
      {evaluation?.feedback && <p className="candidate-feedback">{evaluation.feedback}</p>}
    </div>
  );
}

export default function StageDetail({ stageKey, run }) {
  if (!run) {
    return (
      <div className="stage-detail stage-detail--empty">
        Send a prompt to wake the swarm.
      </div>
    );
  }

  const { candidates = [], evaluations = [], best_index, selection_rationale, final_email } = run;

  if (stageKey === "generator") {
    if (candidates.length === 0) {
      return <div className="stage-detail stage-detail--empty">Waiting for the first draft…</div>;
    }
    return (
      <div className="stage-detail">
        <p className="stage-detail-intro">Three independent drafts from the same prompt.</p>
        <div className="candidate-list">
          {candidates.map((email, i) => (
            <CandidateCard key={i} index={i} email={email} />
          ))}
        </div>
      </div>
    );
  }

  if (stageKey === "evaluator") {
    if (evaluations.length === 0) {
      return <div className="stage-detail stage-detail--empty">Waiting for the first score…</div>;
    }
    return (
      <div className="stage-detail">
        <p className="stage-detail-intro">Each draft scored on clarity, call-to-action, and tone.</p>
        <div className="candidate-list">
          {candidates.map((email, i) => (
            <CandidateCard key={i} index={i} email={email} evaluation={evaluations[i]} />
          ))}
        </div>
      </div>
    );
  }

  if (stageKey === "selector") {
    if (best_index === null || best_index === undefined) {
      return <div className="stage-detail stage-detail--empty">Waiting on a decision…</div>;
    }
    return (
      <div className="stage-detail">
        <p className="stage-detail-intro">
          Version {best_index + 1} moves forward for final polish.
        </p>
        {selection_rationale && <p className="rationale">"{selection_rationale}"</p>}
        <div className="candidate-list">
          <CandidateCard
            index={best_index}
            email={candidates[best_index]}
            evaluation={evaluations[best_index]}
            isBest
          />
        </div>
      </div>
    );
  }

  if (stageKey === "formatter") {
    if (!final_email) {
      return <div className="stage-detail stage-detail--empty">Polishing the final draft…</div>;
    }
    return (
      <div className="stage-detail">
        <p className="stage-detail-intro">Ready to send.</p>
        <pre className="final-email">{final_email}</pre>
      </div>
    );
  }

  return null;
}
