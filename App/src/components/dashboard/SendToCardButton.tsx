import { CreditCard, ChevronRight } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

interface SendToCardButtonProps {
  onClick?: () => void;
}

export const SendToCardButton = ({ onClick }: SendToCardButtonProps) => {
  const navigate = useNavigate();
  const { t } = useTranslation();

  const handleClick = () => {
    if (onClick) {
      onClick();
    } else {
      navigate("/send-to-card");
    }
  };

  return (
    <button
      onClick={handleClick}
      className="w-full karta-card flex items-center justify-between group"
    >
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-[#007AFF] flex items-center justify-center">
          <CreditCard className="w-5 h-5 text-white" />
        </div>
        <div className="text-left">
          <p className="font-medium">{t('dashboard.sendToCard')}</p>
          <p className="text-sm text-muted-foreground">{t('dashboard.sendToCardDescription')}</p>
        </div>
      </div>
      <ChevronRight className="w-5 h-5 text-muted-foreground group-hover:translate-x-1 transition-transform" />
    </button>
  );
};
