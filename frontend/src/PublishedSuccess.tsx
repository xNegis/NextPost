import { OwnerConsultationDetail } from "./OwnerConsultationDetail";

interface PublishedSuccessProps {
  consultationId: string;
  onBack: () => void;
  onViewInMyConsultations?: () => void;
  onSessionLost: () => void;
}

export function PublishedSuccess({
  consultationId,
  onBack,
  onViewInMyConsultations,
  onSessionLost,
}: PublishedSuccessProps) {
  return (
    <OwnerConsultationDetail
      consultationId={consultationId}
      variant="success"
      onBack={onBack}
      onViewInMyConsultations={onViewInMyConsultations}
      onSessionLost={onSessionLost}
    />
  );
}
