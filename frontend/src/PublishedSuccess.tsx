import type { MyConsultationState } from "./consultationApi";
import { OwnerConsultationDetail } from "./OwnerConsultationDetail";

interface PublishedSuccessProps {
  consultationId: string;
  onBack: () => void;
  onViewInMyConsultations?: () => void;
  onDeleted?: (state: MyConsultationState) => void;
  onSessionLost: () => void;
}

export function PublishedSuccess({
  consultationId,
  onBack,
  onViewInMyConsultations,
  onDeleted,
  onSessionLost,
}: PublishedSuccessProps) {
  return (
    <OwnerConsultationDetail
      consultationId={consultationId}
      variant="success"
      onBack={onBack}
      onViewInMyConsultations={onViewInMyConsultations}
      onDeleted={onDeleted}
      onSessionLost={onSessionLost}
    />
  );
}
