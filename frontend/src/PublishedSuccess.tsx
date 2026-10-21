import type { MyConsultationState } from "./consultationApi";
import { OwnerConsultationDetail } from "./OwnerConsultationDetail";

interface PublishedSuccessProps {
  consultationId: string;
  onBack: () => void;
  onViewInMyConsultations?: () => void;
  onDeleted?: (state: MyConsultationState) => void;
  onFinalized?: (consultationId: string) => void;
  onSessionLost: () => void;
}

export function PublishedSuccess({
  consultationId,
  onBack,
  onViewInMyConsultations,
  onDeleted,
  onFinalized,
  onSessionLost,
}: PublishedSuccessProps) {
  return (
    <OwnerConsultationDetail
      consultationId={consultationId}
      variant="success"
      onBack={onBack}
      onViewInMyConsultations={onViewInMyConsultations}
      onDeleted={onDeleted}
      onFinalized={onFinalized}
      onSessionLost={onSessionLost}
    />
  );
}
