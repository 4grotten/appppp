import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { MobileLayout } from "@/components/layout/MobileLayout";
import { useTranslation } from "react-i18next";

interface AccountOption {
  id: string;
  title: string;
  description: string;
  required: string;
  charge: string;
  disabled?: boolean;
}

const TopUpBank = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [selectedAccount, setSelectedAccount] = useState<string>("wire-aed");

  const accountOptions: AccountOption[] = [
    {
      id: "wire-aed",
      title: t("topUp.wireAed"),
      description: t("topUp.wireAedDesc"),
      required: "Emirates ID",
      charge: "5 AED",
    },
    {
      id: "swift",
      title: t("topUp.swift"),
      description: t("topUp.swiftDesc"),
      required: "Emirates ID, Proof of Address",
      charge: "15 AED",
      disabled: true,
    },
  ];

  const handleContinue = () => {
    // Navigate to bank details page or next step
    navigate("/top-up/bank/details");
  };

  return (
    <MobileLayout
      showBackButton
      onBack={() => navigate(-1)}
    >
      <div className="flex flex-col min-h-[calc(100vh-56px)]">
        {/* Title */}
        <div className="pt-4 pb-2 px-6">
          <h1 className="text-2xl font-bold text-center text-foreground">
            {t("topUp.selectAccount")}
          </h1>
        </div>

        {/* Transaction Rates Link */}
        <button className="flex items-center justify-center gap-1 py-3 text-muted-foreground hover:text-foreground transition-colors">
          <span>{t("topUp.transactionRates")}</span>
          <ChevronRight className="w-4 h-4" />
        </button>

        {/* Account Options */}
        <div className="px-6 space-y-4 flex-1">
          {accountOptions.map((option) => (
            <button
              key={option.id}
              onClick={() => {
                if (option.disabled) return;
                if (option.id === "wire-aed") {
                  navigate("/top-up/bank/details");
                } else {
                  setSelectedAccount(option.id);
                }
              }}
              disabled={option.disabled}
              className={`w-full text-left p-5 rounded-2xl transition-all ${
                option.disabled
                  ? "bg-muted/50 opacity-50 cursor-not-allowed"
                  : selectedAccount === option.id
                  ? "bg-muted ring-2 ring-foreground"
                  : "bg-muted hover:bg-muted/80"
              }`}
            >
              <div className="flex items-start gap-3">
                {/* Radio Button */}
                <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-0.5 ${
                  selectedAccount === option.id && !option.disabled
                    ? "border-foreground"
                    : "border-muted-foreground/40"
                }`}>
                  {selectedAccount === option.id && !option.disabled && (
                    <div className="w-3 h-3 rounded-full bg-foreground" />
                  )}
                </div>

                {/* Content */}
                <div className="flex-1">
                  <h3 className={`font-semibold text-lg mb-1 ${
                    option.disabled ? "text-muted-foreground" : "text-foreground"
                  }`}>
                    {option.title}
                  </h3>
                  <p className={`text-sm mb-3 ${
                    option.disabled ? "text-muted-foreground/60" : "text-muted-foreground"
                  }`}>
                    {option.description}
                  </p>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-muted-foreground">• {t("topUp.required")}</span>
                        <span className={option.disabled ? "text-muted-foreground" : "font-semibold text-foreground"}>
                          {option.required}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-muted-foreground">• {t("topUp.charge")}</span>
                        <span className={option.disabled ? "text-muted-foreground" : "font-semibold text-foreground"}>
                          {option.charge}
                        </span>
                      </div>
                    </div>
                </div>
              </div>
            </button>
          ))}
        </div>

        {/* Continue Button */}
        <div className="p-6">
          <button
            onClick={handleContinue}
            disabled={!selectedAccount}
            className="w-full bg-primary text-white font-semibold py-4 rounded-xl hover:bg-primary/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed backdrop-blur-2xl border-2 border-white/50 shadow-lg active:scale-95"
          >
            {t("topUp.continue")}
          </button>
        </div>
      </div>
    </MobileLayout>
  );
};

export default TopUpBank;
