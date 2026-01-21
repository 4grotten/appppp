import { Lock, Shield, CreditCard, Wallet } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { MobileLayout } from "@/components/layout/MobileLayout";
import { PoweredByFooter } from "@/components/layout/PoweredByFooter";
import { motion } from "framer-motion";

const PrivacyProtection = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();

  const benefits = [
    { icon: Shield, textKey: "verify.privacy.benefit1" },
    { icon: CreditCard, textKey: "verify.privacy.benefit2" },
    { icon: Wallet, textKey: "verify.privacy.benefit3" },
  ];

  return (
    <MobileLayout
      showBackButton
      onBack={() => navigate("/")}
      rightAction={<span className="text-sm text-muted-foreground">•••</span>}
    >
      <div className="flex flex-col h-[calc(100vh-56px)]">
        <div className="flex-1 overflow-y-auto px-6 py-8 pb-28">
          {/* Icon */}
          <div className="flex flex-col items-center justify-center text-center">
            <div className="w-24 h-24 rounded-full bg-primary/10 flex items-center justify-center mb-6">
              <Lock className="w-12 h-12 text-primary" />
            </div>

            <h1 className="text-2xl font-bold mb-4 whitespace-pre-line">
              {t('verify.privacy.title')}
            </h1>

            <p className="text-muted-foreground mb-8 whitespace-pre-line">
              {t('verify.privacy.description')}
            </p>

            {/* Benefits */}
            <div className="w-full space-y-3">
              {benefits.map((benefit, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 + index * 0.15, duration: 0.4, ease: "easeOut" }}
                  className="flex items-center gap-2 bg-[#007AFF] text-white text-sm px-4 py-2 rounded-full"
                >
                  <benefit.icon className="w-4 h-4" />
                  <span>{t(benefit.textKey)}</span>
                </motion.div>
              ))}
            </div>
          </div>

          <PoweredByFooter />
        </div>

        {/* Footer */}
        <div className="karta-footer-actions">
          <button
            onClick={() => navigate("/verify/terms")}
            className="karta-btn-primary"
          >
            {t('verify.privacy.button')}
          </button>
        </div>
      </div>
    </MobileLayout>
  );
};

export default PrivacyProtection;
