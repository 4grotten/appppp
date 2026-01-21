import { Fingerprint, ArrowRight } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

interface VerifyIdentityCardProps {
  progress?: number;
  totalSteps?: number;
}

export const VerifyIdentityCard = ({
  progress = 0,
  totalSteps = 3,
}: VerifyIdentityCardProps) => {
  const navigate = useNavigate();
  const { t } = useTranslation();

  return (
    <button
      onClick={() => navigate("/verify")}
      className="w-full rounded-2xl p-4 text-left group bg-[#007AFF]"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          {/* Fingerprint Icon */}
          <div className="w-12 h-12 flex items-center justify-center">
            <Fingerprint className="w-10 h-10 text-white" strokeWidth={1.5} />
          </div>
          
          <div className="flex flex-col">
            <p className="text-[10px] uppercase tracking-wider text-white/70 font-medium">
              {t('dashboard.getYourCard')}
            </p>
            <p className="font-bold text-white text-lg">{t('dashboard.verifyIdentity')}</p>
            <p className="text-sm text-white/70">{t('dashboard.verifyDescription')}</p>
          </div>
        </div>
        
        {/* Arrow Button */}
        <div className="w-10 h-10 min-w-10 min-h-10 shrink-0 rounded-full border-2 border-white flex items-center justify-center group-hover:bg-white/10 transition-colors">
          <ArrowRight className="w-5 h-5 text-white" />
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mt-4 flex gap-2">
        {Array.from({ length: totalSteps }).map((_, index) => (
          <div
            key={index}
            className={`h-1.5 flex-1 rounded-full ${
              index < progress ? "bg-white" : "bg-white/30"
            }`}
          />
        ))}
      </div>

      {/* Steps Counter */}
      <p className="mt-2 text-sm text-white/70 font-medium">
        {progress} {t('dashboard.of')} {totalSteps} {t('dashboard.stepsDone')}
      </p>
    </button>
  );
};
