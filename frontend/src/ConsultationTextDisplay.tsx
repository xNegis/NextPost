import { createElement } from "react";

type HeadingLevel = 1 | 2 | 3 | 4 | 5 | 6;

interface ConsultationTextDisplayProps {
  question: string;
  context: string | null;
  headingLevel?: HeadingLevel;
}

export function ConsultationTextDisplay({
  question,
  context,
  headingLevel = 2,
}: ConsultationTextDisplayProps) {
  const hasContext = context !== null && context !== "";
  return (
    <div className="consultation-text-display">
      {createElement(
        `h${headingLevel}`,
        { className: "consultation-text-display__question", dir: "auto" },
        question,
      )}
      {hasContext && (
        <p className="consultation-text-display__context" dir="auto">
          {context}
        </p>
      )}
    </div>
  );
}
