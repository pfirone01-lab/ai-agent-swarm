const STAGE_META = [
  { key: "generator", label: "Generator", role: "drafts three versions" },
  { key: "evaluator", label: "Evaluator", role: "scores clarity, CTA, tone" },
  { key: "selector", label: "Selector", role: "picks the strongest draft" },
  { key: "formatter", label: "Formatter", role: "polishes the final email" },
];

function nodeState(status) {
  if (status === "done") return "done";
  if (status === "running") return "running";
  if (status === "error") return "error";
  return "pending";
}

export default function PipelineRail({ stages }) {
  return (
    <div className="rail">
      {STAGE_META.map((meta, i) => {
        const stage = stages?.[meta.key] ?? { status: "pending" };
        const state = nodeState(stage.status);
        const isLast = i === STAGE_META.length - 1;
        return (
          <div className="rail-item" key={meta.key}>
            <div className={`rail-node rail-node--${state}`}>
              <span className="rail-node-dot" aria-hidden="true" />
              <span className="rail-node-text">
                <span className="rail-node-label">{meta.label}</span>
                <span className="rail-node-role">{meta.role}</span>
                {state === "running" && stage.detail && (
                  <span className="rail-node-detail">{stage.detail}</span>
                )}
              </span>
            </div>
            {!isLast && (
              <div className={`rail-connector ${state === "done" ? "rail-connector--lit" : ""}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
