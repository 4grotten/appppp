import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { MobileLayout } from "@/components/layout/MobileLayout";
import { PoweredByFooter } from "@/components/layout/PoweredByFooter";
import { StepIndicator } from "@/components/verification/StepIndicator";
import { RadioGroup } from "@/components/verification/RadioGroup";
import { ChevronDown } from "lucide-react";

const DocumentType = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [country] = useState("United Arab Emirates");
  const [documentType, setDocumentType] = useState<string | null>(null);

  const documentTypes = [
    { id: "drivers-license", label: t('verify.documentType.driversLicense') },
    { id: "id-card", label: t('verify.documentType.idCard') },
    { id: "residence-permit", label: t('verify.documentType.residencePermit') },
    { id: "passport", label: t('verify.documentType.passport') },
  ];

  return (
    <MobileLayout
      showBackButton
      onBack={() => navigate("/verify/monthly-volume")}
    >
      <div className="flex flex-col h-[calc(100vh-56px)]">
        {/* Progress */}
        <div className="px-6 py-4">
          <StepIndicator currentStep={3} totalSteps={4} />
        </div>

        <div className="flex-1 px-6 py-4 overflow-y-auto pb-28">
          <h1 className="text-2xl font-bold mb-2">
            {t('verify.documentType.title')}
          </h1>
          <p className="text-muted-foreground mb-6">{t('verify.documentType.subtitle')}</p>

          {/* Issuing Country */}
          <div className="mb-6">
            <label className="text-sm font-medium mb-2 block">
              {t('verify.documentType.issuingCountry')} <span className="text-destructive">*</span>
            </label>
            <button className="w-full flex items-center justify-between p-4 rounded-xl border border-border hover:border-muted-foreground transition-colors">
              <div className="flex items-center gap-2">
                <span className="text-xl">🇦🇪</span>
                <span>{country}</span>
              </div>
              <ChevronDown className="w-5 h-5 text-muted-foreground" />
            </button>
          </div>

          {/* Document Type */}
          <div className="mb-6">
            <label className="text-sm font-medium mb-2 block">
              {t('verify.documentType.documentType')} <span className="text-destructive">*</span>
            </label>
            <RadioGroup
              options={documentTypes}
              value={documentType}
              onChange={setDocumentType}
            />
          </div>

          <p className="text-xs text-muted-foreground">{t('verify.documentType.requiredFields')}</p>

          <PoweredByFooter />
        </div>

        {/* Button */}
        <div className="karta-footer-actions">
          <button
            onClick={() => navigate("/verify/document-upload")}
            disabled={!documentType}
            className={`karta-btn-primary ${
              !documentType ? "opacity-50 cursor-not-allowed" : ""
            }`}
          >
            {t('verify.documentType.continue')}
          </button>
        </div>
      </div>
    </MobileLayout>
  );
};

export default DocumentType;
