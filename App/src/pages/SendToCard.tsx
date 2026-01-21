import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronLeft, CreditCard, Check, ClipboardPaste } from "lucide-react";
import { useTranslation } from "react-i18next";
import { MobileLayout } from "@/components/layout/MobileLayout";
import { PoweredByFooter } from "@/components/layout/PoweredByFooter";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CARD_TO_CARD_FEE_PERCENT } from "@/lib/fees";

// Mock data for cards
const userCards = [
  { id: "1", name: "Visa Virtual", lastFour: "7617", balance: 213757.49, type: "virtual" },
  { id: "2", name: "Visa Metal", lastFour: "4521", balance: 256508.98, type: "metal" },
];

// Mock function to get recipient name by card number
const getRecipientName = (cardNumber: string): string | null => {
  const cleanNumber = cardNumber.replace(/\s/g, "");
  if (cleanNumber.length === 16) {
    // Simulate API response
    const mockNames: Record<string, string> = {
      "4532890123457890": "JOHN SMITH",
      "5425233430109903": "ANNA JOHNSON",
    };
    return mockNames[cleanNumber] || "RECIPIENT NAME";
  }
  return null;
};

// Format card number with spaces
const formatCardNumber = (value: string): string => {
  const cleaned = value.replace(/\D/g, "").slice(0, 16);
  const groups = cleaned.match(/.{1,4}/g);
  return groups ? groups.join(" ") : cleaned;
};

type Step = "card" | "amount" | "confirm";

const SendToCard = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [step, setStep] = useState<Step>("card");
  const [cardNumber, setCardNumber] = useState("");
  const [recipientName, setRecipientName] = useState<string | null>(null);
  const [amount, setAmount] = useState("");
  const [selectedCardId, setSelectedCardId] = useState(userCards[0].id);
  const [isLoading, setIsLoading] = useState(false);

  const selectedCard = userCards.find((c) => c.id === selectedCardId);
  const cleanCardNumber = cardNumber.replace(/\s/g, "");
  const isCardValid = cleanCardNumber.length === 16;
  
  // Parse amount removing commas for calculations
  const parseAmount = (value: string): number => {
    return parseFloat(value.replace(/,/g, "")) || 0;
  };
  
  const numericAmount = parseAmount(amount);
  const isAmountValid = numericAmount > 0 && numericAmount <= (selectedCard?.balance || 0);

  // Check recipient name when card number is complete
  useEffect(() => {
    if (isCardValid) {
      setIsLoading(true);
      // Simulate API delay
      const timer = setTimeout(() => {
        const name = getRecipientName(cardNumber);
        setRecipientName(name);
        setIsLoading(false);
      }, 500);
      return () => clearTimeout(timer);
    } else {
      setRecipientName(null);
    }
  }, [cardNumber, isCardValid]);

  const handleCardNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatCardNumber(e.target.value);
    setCardNumber(formatted);
  };

  const handlePasteFromClipboard = async () => {
    try {
      const text = await navigator.clipboard.readText();
      const formatted = formatCardNumber(text);
      setCardNumber(formatted);
    } catch (err) {
      console.error("Failed to read clipboard");
    }
  };

  const handleAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Remove everything except digits and decimal point
    let value = e.target.value.replace(/[^0-9.]/g, "");
    
    // Prevent multiple decimals
    const parts = value.split(".");
    if (parts.length > 2) return;
    if (parts[1] && parts[1].length > 2) return;
    
    // Format with thousand separators
    if (parts[0]) {
      parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }
    
    setAmount(parts.join("."));
  };

  const handleNext = () => {
    if (step === "card" && isCardValid && recipientName) {
      setStep("amount");
    } else if (step === "amount" && isAmountValid) {
      setStep("confirm");
    }
  };

  const handleBack = () => {
    if (step === "amount") {
      setStep("card");
    } else if (step === "confirm") {
      setStep("amount");
    } else {
      navigate(-1);
    }
  };

  const handleConfirm = () => {
    // Simulate transfer
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      navigate("/");
    }, 1500);
  };

  const fee = numericAmount * (CARD_TO_CARD_FEE_PERCENT / 100);
  const totalAmount = numericAmount + fee;

  return (
    <MobileLayout
      header={
        <button
          onClick={handleBack}
          className="flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors"
        >
          <ChevronLeft className="w-5 h-5" />
          <span className="text-sm">{t('send.back')}</span>
        </button>
      }
    >
      <div className="px-4 py-6 pb-32 space-y-6">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-2xl font-bold">{t('send.sendToCard')}</h1>
          <p className="text-muted-foreground text-sm mt-1">{t('send.easyCardTransfer')}</p>
        </div>

        {/* Progress Indicator */}
        <div className="flex items-center justify-center gap-2">
          {["card", "amount", "confirm"].map((s, i) => (
            <div key={s} className="flex items-center gap-2">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${
                  step === s
                    ? "bg-[#007AFF] text-white"
                    : ["card", "amount", "confirm"].indexOf(step) > i
                    ? "bg-green-500 text-white"
                    : "bg-secondary text-muted-foreground"
                }`}
              >
                {["card", "amount", "confirm"].indexOf(step) > i ? (
                  <Check className="w-4 h-4" />
                ) : (
                  i + 1
                )}
              </div>
              {i < 2 && (
                <div
                  className={`w-8 h-0.5 ${
                    ["card", "amount", "confirm"].indexOf(step) > i
                      ? "bg-green-500"
                      : "bg-secondary"
                  }`}
                />
              )}
            </div>
          ))}
        </div>

        {/* Step 1: Card Number */}
        {step === "card" && (
          <div className="space-y-4 animate-fade-in">
            <div className="space-y-2">
              <label className="text-sm font-medium">{t('send.cardNumber')}</label>
              <div className="relative">
                <Input
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  placeholder="0000 0000 0000 0000"
                  value={cardNumber}
                  onChange={handleCardNumberChange}
                  className="text-lg font-mono tracking-wider h-14 pr-12 no-underline decoration-transparent"
                  maxLength={19}
                />
                <button
                  type="button"
                  onClick={handlePasteFromClipboard}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-lg hover:bg-secondary transition-colors"
                  aria-label="Paste from clipboard"
                >
                  <ClipboardPaste className="w-5 h-5 text-muted-foreground" />
                </button>
              </div>
            </div>

            {isLoading && (
              <div className="bg-secondary rounded-xl p-4 animate-pulse">
                <div className="h-4 bg-muted rounded w-1/2" />
              </div>
            )}

            {recipientName && !isLoading && (
              <div className="bg-secondary rounded-xl p-4 flex items-center gap-3 animate-fade-in">
                <div className="w-10 h-10 rounded-full bg-green-500 flex items-center justify-center">
                  <Check className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{t('send.recipient')}</p>
                  <p className="font-semibold">{recipientName}</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Step 2: Amount */}
        {step === "amount" && (
          <div className="space-y-4 animate-fade-in">
            {/* Recipient Preview */}
            <div className="bg-secondary rounded-xl p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-[#007AFF] flex items-center justify-center">
                <CreditCard className="w-5 h-5 text-white" />
              </div>
              <div>
                <p className="font-medium">{recipientName}</p>
                <p className="text-sm text-muted-foreground no-underline decoration-transparent">{cardNumber}</p>
              </div>
            </div>

            {/* Select Source Card */}
            <div className="space-y-2">
              <label className="text-sm font-medium">{t('send.fromCard')}</label>
              <Select value={selectedCardId} onValueChange={setSelectedCardId}>
                <SelectTrigger className="h-14 rounded-xl">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {userCards.map((card) => (
                    <SelectItem key={card.id} value={card.id}>
                      <div className="flex items-center justify-between w-full gap-4">
                        <span>{card.name} •••• {card.lastFour}</span>
                        <span className="text-muted-foreground">{card.balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} AED</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-sm text-muted-foreground">
                {t('send.available')}: <span className="font-medium text-foreground">{selectedCard?.balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} AED</span>
              </p>
            </div>

            {/* Amount Input */}
            <div className="space-y-2">
              <label className="text-sm font-medium">{t('send.amount')}</label>
              <div className="relative">
                <Input
                  type="text"
                  inputMode="decimal"
                  placeholder="0.00"
                  value={amount}
                  onChange={handleAmountChange}
                  className="text-2xl font-bold h-16 pr-28"
                />
                <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      // Max amount considering fee: balance = amount * (1 + fee/100)
                      const maxAmount = (selectedCard?.balance || 0) / (1 + CARD_TO_CARD_FEE_PERCENT / 100);
                      const formatted = maxAmount.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
                      setAmount(formatted);
                    }}
                    className="px-2 py-1 text-xs font-bold bg-[#007AFF] text-white rounded-md hover:bg-[#0066DD] transition-colors"
                  >
                    MAX
                  </button>
                  <span className="text-muted-foreground font-medium">AED</span>
                </div>
              </div>
              {numericAmount > (selectedCard?.balance || 0) && (
                <p className="text-sm text-red-500">{t('send.insufficientBalance')}</p>
              )}
              {numericAmount > 0 && numericAmount <= (selectedCard?.balance || 0) && (
                <div className="flex justify-between text-sm text-muted-foreground">
                  <span>{t('send.fee')} ({CARD_TO_CARD_FEE_PERCENT}%): {fee.toFixed(2)} AED</span>
                  <span>{t('send.total')}: {totalAmount.toFixed(2)} AED</span>
                </div>
              )}
            </div>

            {/* Quick Amount Buttons */}
            <div className="grid grid-cols-4 gap-2">
              {[50, 100, 250, 500].map((quickAmount) => (
                <Button
                  key={quickAmount}
                  variant="outline"
                  className="rounded-xl"
                  onClick={() => setAmount(quickAmount.toString())}
                  disabled={quickAmount > (selectedCard?.balance || 0)}
                >
                  {quickAmount}
                </Button>
              ))}
            </div>
          </div>
        )}

        {/* Step 3: Confirm */}
        {step === "confirm" && (
          <div className="space-y-4 animate-fade-in">
            <div className="bg-secondary rounded-2xl p-5 space-y-4">
              <div className="text-center pb-4 border-b border-border">
                <p className="text-sm text-muted-foreground mb-1">{t('send.youreSending')}</p>
                <p className="text-3xl font-bold">{numericAmount.toFixed(2)} AED</p>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">{t('send.to')}</span>
                  <span className="font-medium">{recipientName}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">{t('send.card')}</span>
                  <span className="font-mono no-underline decoration-transparent">{cardNumber}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">{t('send.from')}</span>
                  <span className="font-medium">{selectedCard?.name} •••• {selectedCard?.lastFour}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">{t('send.fee')} ({CARD_TO_CARD_FEE_PERCENT}%)</span>
                  <span>{fee.toFixed(2)} AED</span>
                </div>
                <div className="flex justify-between pt-3 border-t border-border">
                  <span className="font-medium">{t('send.total')}</span>
                  <span className="font-bold">{totalAmount.toFixed(2)} AED</span>
                </div>
              </div>
            </div>

            <p className="text-xs text-center text-muted-foreground">
              {t('send.transferTerms')}
            </p>

            <PoweredByFooter />
          </div>
        )}

        {/* Footer for other steps */}
        {step !== "confirm" && (
          <div className="pt-4">
            <PoweredByFooter />
          </div>
        )}
      </div>

      {/* Fixed Bottom Button */}
      <div className="fixed bottom-0 left-0 right-0 p-6 max-w-[800px] mx-auto">
        {step === "card" && (
          <Button
            className="w-full h-14 text-base font-semibold bg-primary/90 hover:bg-primary text-white rounded-xl active:scale-95 backdrop-blur-2xl border-2 border-white/50 shadow-lg transition-all"
            disabled={!isCardValid || !recipientName || isLoading}
            onClick={handleNext}
          >
            {t('send.continue')}
          </Button>
        )}
        {step === "amount" && (
          <Button
            className="w-full h-14 text-base font-semibold bg-primary/90 hover:bg-primary text-white rounded-xl active:scale-95 backdrop-blur-2xl border-2 border-white/50 shadow-lg transition-all"
            disabled={!isAmountValid}
            onClick={handleNext}
          >
            {t('send.continue')}
          </Button>
        )}
        {step === "confirm" && (
          <Button
            className="w-full h-14 text-base font-semibold bg-primary/90 hover:bg-primary text-white rounded-xl active:scale-95 backdrop-blur-2xl border-2 border-white/50 shadow-lg transition-all"
            onClick={handleConfirm}
            disabled={isLoading}
          >
            {isLoading ? t('send.processing') : t('send.confirmTransfer')}
          </Button>
        )}
      </div>
    </MobileLayout>
  );
};

export default SendToCard;
