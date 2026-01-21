import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronLeft, ArrowRight, ClipboardPaste, ChevronDown, Check, CreditCard } from "lucide-react";
import { useTranslation } from "react-i18next";
import { MobileLayout } from "@/components/layout/MobileLayout";
import { PoweredByFooter } from "@/components/layout/PoweredByFooter";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
} from "@/components/ui/drawer";
import { BANK_TRANSFER_FEE_PERCENT } from "@/lib/fees";

interface Card {
  id: string;
  type: "virtual" | "metal";
  name: string;
  lastFour: string;
  balance: number;
}

const cards: Card[] = [
  { id: "1", type: "virtual", name: "Visa Virtual", lastFour: "4532", balance: 213757.49 },
  { id: "2", type: "metal", name: "Visa Metal", lastFour: "8901", balance: 256508.98 },
];

const SendBank = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [step, setStep] = useState(1);
  const [selectedCard, setSelectedCard] = useState<Card>(cards[0]);
  const [cardDrawerOpen, setCardDrawerOpen] = useState(false);
  
  // Step 1: IBAN
  const [iban, setIban] = useState("");
  
  // Step 2: Recipient details
  const [recipientName, setRecipientName] = useState("");
  const [bankName, setBankName] = useState("");
  
  // Step 3: Amount
  const [amountAED, setAmountAED] = useState("");

  const transferFee = amountAED ? (parseFloat(amountAED) * BANK_TRANSFER_FEE_PERCENT / 100).toFixed(2) : "0.00";
  const totalAmount = amountAED ? (parseFloat(amountAED) + parseFloat(transferFee)).toFixed(2) : "0.00";

  const formatIban = (value: string) => {
    // Remove all non-alphanumeric characters
    const cleaned = value.replace(/[^A-Za-z0-9]/g, "").toUpperCase();
    // Add spaces every 4 characters
    const formatted = cleaned.match(/.{1,4}/g)?.join(" ") || cleaned;
    return formatted.slice(0, 29); // IBAN max length with spaces
  };

  const formatAmountInput = (value: string) => {
    // Remove everything except digits and decimal point
    const cleaned = value.replace(/[^\d.]/g, "");
    const parts = cleaned.split(".");
    if (parts.length > 2) return amountAED;
    if (parts[1] && parts[1].length > 2) {
      return `${parts[0]}.${parts[1].slice(0, 2)}`;
    }
    return cleaned;
  };

  const formatDisplayAmount = (value: string) => {
    if (!value) return "";
    const num = parseFloat(value);
    if (isNaN(num)) return value;
    const parts = value.split(".");
    const integerPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    if (parts.length > 1) {
      return `${integerPart}.${parts[1]}`;
    }
    return integerPart;
  };

  const parseDisplayAmount = (value: string) => {
    return value.replace(/,/g, "");
  };

  const isStep1Valid = iban.replace(/\s/g, "").length >= 15;
  const isStep2Valid = recipientName.trim().length >= 2 && bankName.trim().length >= 2;
  const isStep3Valid = parseFloat(amountAED) > 0 && parseFloat(totalAmount) <= selectedCard.balance;

  const handleNext = () => {
    if (step < 3) {
      setStep(step + 1);
    } else {
      // Submit transfer
      navigate("/");
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1);
    } else {
      navigate(-1);
    }
  };

  const getStepValid = () => {
    switch (step) {
      case 1: return isStep1Valid;
      case 2: return isStep2Valid;
      case 3: return isStep3Valid;
      default: return false;
    }
  };

  return (
    <>
      <MobileLayout
        header={
          <button
            onClick={handleBack}
            className="flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors"
          >
            <ChevronLeft className="w-5 h-5" />
            <span className="text-sm">{t("send.back")}</span>
          </button>
        }
      >
        <div className="px-4 py-6 pb-32 space-y-6">
          {/* Header */}
          <div>
            <h1 className="text-2xl font-bold">{t("send.sendLocalBankTransfer")}</h1>
            <p className="text-muted-foreground text-sm mt-1">
              {t("send.stepOf", { step, total: 3 })}
            </p>
          </div>

          {/* Progress Bar */}
          <div className="flex gap-2">
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                className={`flex-1 h-1 rounded-full transition-colors ${
                  s <= step ? "bg-primary" : "bg-muted"
                }`}
              />
            ))}
          </div>

          {/* Step 1: IBAN */}
          {step === 1 && (
            <div className="space-y-6">
              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">
                  {t("send.recipientIban")}
                </label>
                <div className="relative">
                  <Input
                    value={iban}
                    onChange={(e) => setIban(formatIban(e.target.value))}
                    placeholder="AE07 0331 2345 6789 0123 456"
                    className="h-14 rounded-2xl bg-secondary border-0 text-base font-mono pr-12"
                    inputMode="text"
                  />
                  <button
                    type="button"
                    onClick={async () => {
                      try {
                        const text = await navigator.clipboard.readText();
                        setIban(formatIban(text));
                      } catch (err) {
                        console.error("Failed to read clipboard");
                      }
                    }}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-lg hover:bg-background/50 transition-colors"
                    aria-label="Paste from clipboard"
                  >
                    <ClipboardPaste className="w-5 h-5 text-muted-foreground" />
                  </button>
                </div>
                <p className="text-xs text-muted-foreground">
                  {t("send.enterIban")}
                </p>
              </div>
            </div>
          )}

          {/* Step 2: Recipient Details */}
          {step === 2 && (
            <div className="space-y-6">
              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">
                  {t("send.recipientName")}
                </label>
                <Input
                  value={recipientName}
                  onChange={(e) => setRecipientName(e.target.value)}
                  placeholder="John Smith"
                  className="h-14 rounded-2xl bg-secondary border-0 text-base"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">
                  {t("send.bankName")}
                </label>
                <Input
                  value={bankName}
                  onChange={(e) => setBankName(e.target.value)}
                  placeholder="Emirates NBD"
                  className="h-14 rounded-2xl bg-secondary border-0 text-base"
                />
              </div>
            </div>
          )}

          {/* Step 3: Amount */}
          {step === 3 && (
            <div className="space-y-6">
              {/* Card Selection */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">
                  {t("send.fromCard")}
                </label>
                <button
                  onClick={() => setCardDrawerOpen(true)}
                  className="w-full flex items-center justify-between p-4 bg-secondary rounded-2xl hover:bg-muted/80 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      selectedCard.type === "metal" 
                        ? "bg-gradient-to-br from-zinc-400 to-zinc-600" 
                        : "bg-primary"
                    }`}>
                      <CreditCard className="w-5 h-5 text-primary-foreground" />
                    </div>
                    <div className="text-left">
                      <p className="font-semibold">{selectedCard.name}</p>
                      <p className="text-sm text-muted-foreground">
                        •••• {selectedCard.lastFour}
                      </p>
                    </div>
                  </div>
                  <ChevronDown className="w-5 h-5 text-muted-foreground" />
                </button>
              </div>

              {/* Transfer Details Summary */}
              <div className="bg-secondary rounded-2xl p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground text-sm">{t("send.to")}</span>
                  <span className="font-medium">{recipientName}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground text-sm">{t("send.iban")}</span>
                  <span className="font-medium font-mono text-sm">{iban}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground text-sm">{t("send.bank")}</span>
                  <span className="font-medium">{bankName}</span>
                </div>
              </div>

              {/* Amount Input */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-muted-foreground">
                    {t("send.amount")}
                  </label>
                  <span className="text-sm text-muted-foreground">
                    {t("send.available")}: <span className="font-medium text-foreground">{selectedCard.balance.toLocaleString('en-US', { minimumFractionDigits: 2 })} AED</span>
                  </span>
                </div>
                <div className="relative">
                  <Input
                    value={formatDisplayAmount(amountAED)}
                    onChange={(e) => setAmountAED(formatAmountInput(parseDisplayAmount(e.target.value)))}
                    placeholder="0.00"
                    className="h-14 rounded-2xl bg-secondary border-0 text-base pr-28"
                    inputMode="decimal"
                  />
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
                    <button
                      onClick={() => {
                      const maxAmount = selectedCard.balance / (1 + BANK_TRANSFER_FEE_PERCENT / 100);
                      setAmountAED(maxAmount.toFixed(2));
                      }}
                      className="px-3 py-1.5 rounded-xl bg-primary/10 text-primary text-xs font-bold hover:bg-primary/20 transition-colors"
                    >
                      MAX
                    </button>
                    <span className="text-muted-foreground font-medium">
                      AED
                    </span>
                  </div>
                </div>
              </div>

              {/* Fee Breakdown */}
              <div className="bg-secondary rounded-2xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">{t("send.transferAmount")}</span>
                  <span className="font-medium">{parseFloat(amountAED || "0").toLocaleString('en-US', { minimumFractionDigits: 2 })} AED</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">{t("send.transferFee")} ({BANK_TRANSFER_FEE_PERCENT}%)</span>
                  <span className="font-medium text-[#FFA000]">+{parseFloat(transferFee).toLocaleString('en-US', { minimumFractionDigits: 2 })} AED</span>
                </div>
                <div className="flex items-center justify-between pt-2 border-t border-border">
                  <span className="text-muted-foreground">{t("send.total")}</span>
                  <span className="font-semibold text-lg">{parseFloat(totalAmount).toLocaleString('en-US', { minimumFractionDigits: 2 })} AED</span>
                </div>
              </div>

              {parseFloat(totalAmount) > selectedCard.balance && (
                <div className="bg-red-500/10 rounded-2xl p-4">
                  <p className="text-sm text-red-500">
                    ⚠️ {t("send.insufficientBalanceWarning")}
                  </p>
                </div>
              )}
            </div>
          )}

          <div className="pt-4">
            <PoweredByFooter />
          </div>
        </div>

        {/* Fixed Continue Button */}
        <div className="fixed bottom-0 left-0 right-0 p-6 max-w-[800px] mx-auto">
          <Button
            onClick={handleNext}
            disabled={!getStepValid()}
            className="w-full h-14 rounded-2xl text-base font-semibold bg-primary/90 hover:bg-primary active:scale-95 backdrop-blur-2xl border-2 border-white/50 shadow-lg transition-all"
          >
            {step === 3 ? (
              `${t("send.continue")} ${parseFloat(amountAED || "0").toLocaleString('en-US', { minimumFractionDigits: 2 })} AED`
            ) : (
              <span className="flex items-center gap-2">
                {t("send.continue")}
                <ArrowRight className="w-5 h-5" />
              </span>
            )}
          </Button>
        </div>
      </MobileLayout>

      {/* Card Selection Drawer */}
      <Drawer open={cardDrawerOpen} onOpenChange={setCardDrawerOpen}>
        <DrawerContent className="bg-background">
          <DrawerHeader className="pb-2">
            <DrawerTitle className="text-xl font-semibold text-center">
              {t("send.selectCard")}
            </DrawerTitle>
          </DrawerHeader>
          <div className="px-4 pb-8 space-y-3">
            {cards.map((card) => (
              <button
                key={card.id}
                onClick={() => {
                  setSelectedCard(card);
                  setCardDrawerOpen(false);
                }}
                className="w-full flex items-center gap-4 p-4 bg-muted rounded-2xl hover:bg-muted/80 transition-colors"
              >
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                  card.type === "metal" 
                    ? "bg-gradient-to-br from-zinc-400 to-zinc-600" 
                    : "bg-primary"
                }`}>
                  <CreditCard className="w-6 h-6 text-primary-foreground" />
                </div>
                <div className="flex-1 text-left">
                  <p className="font-semibold text-foreground">{card.name}</p>
                  <p className="text-sm text-muted-foreground">
                    •••• {card.lastFour} · {card.balance.toLocaleString('en-US', { minimumFractionDigits: 2 })} AED
                  </p>
                </div>
                {selectedCard.id === card.id && (
                  <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center">
                    <Check className="w-4 h-4 text-primary-foreground" />
                  </div>
                )}
              </button>
            ))}
          </div>
        </DrawerContent>
      </Drawer>
    </>
  );
};

export default SendBank;
