import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { MobileLayout } from "@/components/layout/MobileLayout";
import { PoweredByFooter } from "@/components/layout/PoweredByFooter";
import { StepIndicator } from "@/components/verification/StepIndicator";
import { VerificationStepsList } from "@/components/verification/VerificationStepsList";
import { FileText, Camera, Smile } from "lucide-react";

const VerificationSteps = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();

  const steps = [
    {
      id: "questionnaire",
      title: t('verify.steps.questionnaire'),
      icon: <FileText className="w-5 h-5" />,
      status: "current" as const,
    },
    {
      id: "document",
      title: t('verify.steps.document'),
      icon: <Camera className="w-5 h-5" />,
      status: "pending" as const,
    },
    {
      id: "liveness",
      title: t('verify.steps.liveness'),
      icon: <Smile className="w-5 h-5" />,
      status: "pending" as const,
    },
  ];


  return (
    <MobileLayout
      showBackButton
      onBack={() => navigate("/verify/terms")}
    >
      <div className="flex flex-col h-[calc(100vh-56px)]">
        {/* Progress */}
        <div className="px-6 py-4">
          <StepIndicator currentStep={0} totalSteps={4} />
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4 pb-28">
          <h1 className="text-2xl font-bold mb-2">{t('verify.steps.title')}</h1>
          <p className="text-muted-foreground mb-8">
            {t('verify.steps.description')}
          </p>

          <VerificationStepsList steps={steps} />

          <PoweredByFooter />
        </div>


        {/* Button */}
        <div className="karta-footer-actions">
          <button
            onClick={() => navigate("/verify/personal-info")}
            className="karta-btn-primary"
          >
            {t('verify.steps.button')}
          </button>
        </div>
      </div>
    </MobileLayout>
  );
};

export default VerificationSteps;
