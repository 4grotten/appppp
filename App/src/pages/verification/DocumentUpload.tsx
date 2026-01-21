import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { MobileLayout } from "@/components/layout/MobileLayout";
import { PoweredByFooter } from "@/components/layout/PoweredByFooter";
import { StepIndicator } from "@/components/verification/StepIndicator";
import { CreditCard, Sun, PenOff, ExternalLink } from "lucide-react";

const DocumentUpload = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();

  return (
    <MobileLayout
      showBackButton
      onBack={() => navigate("/verify/document-type")}
    >
      <div className="flex flex-col h-[calc(100vh-56px)]">
        {/* Progress */}
        <div className="px-6 py-4">
          <StepIndicator currentStep={3} totalSteps={4} />
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4 pb-28 flex flex-col items-center justify-center">
          <h1 className="text-2xl font-bold mb-2 text-center">
            {t('verify.upload.title')}
          </h1>
          <h2 className="text-2xl font-bold mb-8 text-center">
            {t('verify.upload.driversLicense')}
          </h2>

          {/* Document Icon */}
          <div className="w-32 h-24 border-2 border-dashed border-border rounded-xl flex items-center justify-center mb-8">
            <CreditCard className="w-12 h-12 text-muted-foreground" />
          </div>

          {/* Tips */}
          <div className="w-full space-y-3 mb-8">
            <h3 className="font-semibold">{t('verify.upload.tips')}</h3>
            <div className="flex items-center gap-3 text-sm">
              <div className="w-6 h-6 rounded-full bg-success/20 flex items-center justify-center">
                <Sun className="w-4 h-4 text-success" />
              </div>
              <span>{t('verify.upload.tip1')}</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <div className="w-6 h-6 rounded-full bg-success/20 flex items-center justify-center">
                <Sun className="w-4 h-4 text-success" />
              </div>
              <span>{t('verify.upload.tip2')}</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <div className="w-6 h-6 rounded-full bg-destructive/20 flex items-center justify-center">
                <PenOff className="w-4 h-4 text-destructive" />
              </div>
              <span>{t('verify.upload.tip3')}</span>
            </div>
          </div>

          <button className="flex items-center gap-2 text-primary text-sm">
            <ExternalLink className="w-4 h-4" />
            <span>{t('verify.upload.viewGuidelines')}</span>
          </button>

          <PoweredByFooter />
        </div>

        {/* Button */}
        <div className="karta-footer-actions">
          <button
            onClick={() => navigate("/verify/document-capture-front")}
            className="karta-btn-primary"
          >
            {t('verify.upload.continue')}
          </button>
        </div>
      </div>
    </MobileLayout>
  );
};

export default DocumentUpload;
