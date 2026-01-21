import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { MobileLayout } from "@/components/layout/MobileLayout";
import { PoweredByFooter } from "@/components/layout/PoweredByFooter";
import { CheckCircle, FileText, Smile, AlertCircle } from "lucide-react";

const VerificationComplete = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();

  const steps = [
    {
      id: "personal",
      titleKey: "verify.complete.personalInfo",
      status: "resubmit" as const,
      icon: <AlertCircle className="w-5 h-5" />,
    },
    {
      id: "document",
      titleKey: "verify.complete.identityDocument",
      status: "submitted" as const,
      icon: <FileText className="w-5 h-5" />,
    },
    {
      id: "liveness",
      titleKey: "verify.complete.livenessCheck",
      status: "submitted" as const,
      icon: <Smile className="w-5 h-5" />,
    },
  ];

  return (
    <MobileLayout
      showBackButton
      onBack={() => navigate("/")}
    >
      <div className="flex flex-col h-[calc(100vh-56px)]">
        <div className="flex-1 overflow-y-auto px-6 py-8 pb-28">
          <h1 className="text-2xl font-bold mb-2">
            {t('verify.complete.title')}
          </h1>
          <p className="text-muted-foreground mb-8">
            {t('verify.complete.description')}
          </p>

          {/* Needs Resubmission */}
          <div className="mb-6">
            <p className="text-sm font-medium text-muted-foreground mb-3">
              {t('verify.complete.needsResubmission')}
            </p>
            {steps
              .filter((s) => s.status === "resubmit")
              .map((step) => (
                <div
                  key={step.id}
                  className="flex items-center gap-3 p-4 rounded-xl border border-destructive/30 bg-destructive/5"
                >
                  <div className="w-10 h-10 rounded-full bg-destructive/20 flex items-center justify-center text-destructive">
                    {step.icon}
                  </div>
                  <div>
                    <p className="text-sm text-destructive font-medium">
                      {t('verify.complete.resubmit')}
                    </p>
                    <p className="font-medium">{t(step.titleKey)}</p>
                  </div>
                </div>
              ))}
          </div>

          {/* All Good */}
          <div>
            <p className="text-sm font-medium text-muted-foreground mb-3">
              {t('verify.complete.allGood')}
            </p>
            <div className="space-y-3">
              {steps
                .filter((s) => s.status === "submitted")
                .map((step) => (
                  <div
                    key={step.id}
                    className="flex items-center gap-3 p-4 rounded-xl border border-success/30 bg-success/5"
                  >
                    <div className="w-10 h-10 rounded-full bg-success/20 flex items-center justify-center text-success">
                      <CheckCircle className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-sm text-success font-medium">
                        {t('verify.complete.submitted')}
                      </p>
                      <p className="font-medium">{t(step.titleKey)}</p>
                    </div>
                  </div>
                ))}
            </div>
          </div>

          <PoweredByFooter />
        </div>

        {/* Button */}
        <div className="karta-footer-actions">
          <button onClick={() => navigate("/")} className="karta-btn-primary">
            {t('verify.complete.button')}
          </button>
        </div>
      </div>
    </MobileLayout>
  );
};

export default VerificationComplete;
