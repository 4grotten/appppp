import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { MobileLayout } from "@/components/layout/MobileLayout";
import { PoweredByFooter } from "@/components/layout/PoweredByFooter";
import { StepIndicator } from "@/components/verification/StepIndicator";
import { RadioGroup } from "@/components/verification/RadioGroup";

const volumeOptions = [
  { id: "less-3700", label: "Less than 3,700 AED" },
  { id: "3700-18500", label: "3,700 to 18,500 AED" },
  { id: "18500-37000", label: "18,501 to 37,000 AED" },
  { id: "37000-92000", label: "37,001 to 92,000 AED" },
  { id: "more-92000", label: "More than 92,000 AED" },
];

const MonthlyVolume = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [volume, setVolume] = useState<string | null>(null);
  const [crypto, setCrypto] = useState<string | null>(null);

  const usageOptions = [
    { id: "yes-regularly", label: t('verify.volume.yesRegularly') },
    { id: "yes-occasionally", label: t('verify.volume.yesOccasionally') },
    { id: "no-interested", label: t('verify.volume.planningToStart') },
  ];

  const isValid = volume && crypto;

  return (
    <MobileLayout
      showBackButton
      onBack={() => navigate("/verify/personal-info")}
    >
      <div className="flex flex-col h-[calc(100vh-56px)]">
        {/* Progress */}
        <div className="px-6 py-4">
          <StepIndicator currentStep={2} totalSteps={4} />
        </div>

        <div className="flex-1 px-6 py-4 overflow-y-auto pb-28">
          <h1 className="text-2xl font-bold mb-6">
            {t('verify.volume.title')}
          </h1>

          {/* Expected Monthly Volume */}
          <div className="mb-6">
            <label className="text-sm font-medium mb-2 block">
              {t('verify.volume.monthlyVolume')}{" "}
              <span className="text-destructive">*</span>
            </label>
            <RadioGroup
              options={volumeOptions}
              value={volume}
              onChange={setVolume}
            />
          </div>

          {/* Card Usage */}
          <div className="mb-6">
            <label className="text-sm font-medium mb-2 block">
              {t('verify.volume.cardUsage')}{" "}
              <span className="text-destructive">*</span>
            </label>
            <RadioGroup
              options={usageOptions}
              value={crypto}
              onChange={setCrypto}
            />
          </div>

          <PoweredByFooter />
        </div>

        {/* Button */}
        <div className="karta-footer-actions">
          <button
            onClick={() => navigate("/verify/document-type")}
            disabled={!isValid}
            className={`karta-btn-primary ${
              !isValid ? "opacity-50 cursor-not-allowed" : ""
            }`}
          >
            {t('verify.volume.continue')}
          </button>
        </div>
      </div>
    </MobileLayout>
  );
};

export default MonthlyVolume;
