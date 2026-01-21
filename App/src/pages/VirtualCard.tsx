import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronLeft, ChevronDown, Lock, RefreshCw, Eye, EyeOff, X, Copy, ChevronUp } from "lucide-react";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import { MobileLayout } from "@/components/layout/MobileLayout";
import { PoweredByFooter } from "@/components/layout/PoweredByFooter";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { CardTransactionsList } from "@/components/card/CardTransactionsList";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

// Animated number component for balance
const AnimatedNumber = ({ value, duration = 800 }: { value: number; duration?: number }) => {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let startTime: number | null = null;
    let animationFrame: number;

    const animate = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      const easeOut = 1 - Math.pow(1 - progress, 3);
      setDisplayValue(value * easeOut);

      if (progress < 1) {
        animationFrame = requestAnimationFrame(animate);
      }
    };

    animationFrame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationFrame);
  }, [value, duration]);

  return <>{displayValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</>;
};

// Virtual card transactions (using IDs from TransactionDetails)
const virtualCardTransactions = [
  {
    date: "January 10",
    totalSpend: 125.87,
    transactions: [
      { id: "1", merchant: "LIFE", time: "13:02", amountUSDT: 8.34, amountLocal: 29.87, localCurrency: "AED", color: "#3B82F6" },
      { id: "2", merchant: "ALAYA", time: "00:59", amountUSDT: 26.80, amountLocal: 96.00, localCurrency: "AED", color: "#22C55E" },
    ],
  },
  {
    date: "December 31",
    totalSpend: 101.06,
    transactions: [
      { id: "5", merchant: "CELLAR", time: "20:48", amountUSDT: 22.06, amountLocal: 79.00, localCurrency: "AED", color: "#EAB308" },
      { id: "6", merchant: "Top up", time: "20:46", amountUSDT: 194.10, amountLocal: 200.00, localCurrency: "USDT", color: "#22C55E", type: "topup" as const },
    ],
  },
  {
    date: "December 21",
    totalSpend: 183.50,
    transactions: [
      { id: "15", merchant: "Annual Card fee", time: "23:31", amountUSDT: 183.50, amountLocal: 183.50, localCurrency: "AED", color: "#CCFF00", type: "card_activation" as const },
      { id: "16", merchant: "Top up", time: "23:30", amountUSDT: 44.10, amountLocal: 50.00, localCurrency: "USDT", color: "#22C55E", type: "topup" as const },
    ],
  },
];

const VirtualCard = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [showDetails, setShowDetails] = useState(false);
  const [billingOpen, setBillingOpen] = useState(false);
  const [balanceVisible, setBalanceVisible] = useState(false);
  const [animationKey, setAnimationKey] = useState(0);

  const cardData = {
    holderName: "RINAT KAMIEV",
    lastFour: "7617",
    fullNumber: "4532 8901 2345 7617",
    expiry: "12/28",
    cvv: "123",
    balance: 213757.49,
  };

  const toggleBalanceVisibility = () => {
    if (!balanceVisible) {
      setAnimationKey(prev => prev + 1);
    }
    setBalanceVisible(!balanceVisible);
  };

  return (
    <MobileLayout
      header={
        <button 
          onClick={() => navigate(-1)}
          className="flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors"
        >
          <ChevronLeft className="w-5 h-5" />
          <span className="text-sm">{t("card.back")}</span>
        </button>
      }
    >
      <motion.div 
        className="px-4 py-6 space-y-5"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4 }}
      >
        {/* Card Visual */}
        <motion.div 
          className="relative w-full aspect-[1.586/1] rounded-2xl overflow-hidden bg-gradient-to-br from-[#c8f542] to-[#a8d535] p-6 flex flex-col justify-between"
          initial={{ opacity: 0, y: 30, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
        >
          {/* Card pattern overlay */}
          <div 
            className="absolute inset-0 opacity-30"
            style={{
              backgroundImage: `repeating-radial-gradient(circle at center, transparent 0, transparent 2px, rgba(0,0,0,0.05) 2px, rgba(0,0,0,0.05) 4px)`,
              backgroundSize: '8px 8px',
            }}
          />
          
          {/* Logo in center */}
          <div className="absolute inset-0 flex items-center justify-center">
            <svg width="60" height="40" viewBox="0 0 60 40" fill="none">
              <path d="M30 5L45 20L30 35L15 20L30 5Z" fill="black" />
              <path d="M30 12L38 20L30 28L22 20L30 12Z" fill="#c8f542" />
            </svg>
          </div>
          
          {/* Cardholder name */}
          <div className="relative mt-auto flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center overflow-hidden">
              <span className="text-xs text-white font-medium">RK</span>
            </div>
            <span className="text-sm font-semibold text-black bg-[#c8f542]/80 px-3 py-1 rounded-full">
              {cardData.holderName}
            </span>
          </div>
          
          {/* Visa logo */}
          <div className="absolute bottom-6 right-6 text-right">
            <span className="text-2xl font-bold text-[#1a1f71] italic tracking-tight">VISA</span>
            <p className="text-xs text-[#1a1f71] font-medium">Signature</p>
          </div>
        </motion.div>

        {/* Apple Pay Banner */}
        <motion.div 
          className="bg-secondary rounded-xl p-4 flex items-center justify-between"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
        >
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/>
              </svg>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M6 8.32a7.43 7.43 0 0 1 0 7.36"/>
                <path d="M9.46 6.21a11.76 11.76 0 0 1 0 11.58"/>
                <path d="M12.91 4.1a15.91 15.91 0 0 1 .01 15.8"/>
                <path d="M16.37 2a20.16 20.16 0 0 1 0 20"/>
              </svg>
            </div>
            <span className="text-sm font-medium">{t("card.addToApplePay")}</span>
          </div>
          <button className="p-1 hover:bg-muted rounded-full transition-colors">
            <X className="w-4 h-4 text-muted-foreground" />
          </button>
        </motion.div>

        {/* Card Details */}
        <motion.div 
          className="space-y-3"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
        >
          {/* Card Number */}
          <div className="bg-secondary rounded-xl p-4 flex items-center justify-between">
            <AnimatePresence mode="wait">
              <motion.span 
                key={showDetails ? "visible" : "hidden"}
                className="text-base font-mono"
                initial={{ opacity: 0, filter: "blur(8px)" }}
                animate={{ opacity: 1, filter: "blur(0px)" }}
                exit={{ opacity: 0, filter: "blur(8px)" }}
                transition={{ duration: 0.25 }}
              >
                {showDetails ? cardData.fullNumber : `•••• •••• •••• ${cardData.lastFour}`}
              </motion.span>
            </AnimatePresence>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  navigator.clipboard.writeText(cardData.fullNumber.replace(/\s/g, ''));
                  toast.success(t("toast.cardNumberCopied"));
                }}
                className="p-2 h-8 w-8 rounded-full bg-secondary hover:bg-muted"
              >
                <Copy className="w-3.5 h-3.5" />
              </Button>
              <Button
                size="sm"
                onClick={() => setShowDetails(!showDetails)}
                className="text-xs font-medium gap-1.5 rounded-full border-none bg-black hover:bg-[#007AFF] text-white"
              >
                {showDetails ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                {showDetails ? t("card.hide") : t("card.reveal")}
              </Button>
            </div>
          </div>

          {/* Expiry and CVV */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-secondary rounded-xl p-4">
              <p className="text-xs text-muted-foreground mb-1">{t("card.expiry")}</p>
              <AnimatePresence mode="wait">
                <motion.p 
                  key={showDetails ? "exp-visible" : "exp-hidden"}
                  className="text-base font-mono"
                  initial={{ opacity: 0, filter: "blur(8px)" }}
                  animate={{ opacity: 1, filter: "blur(0px)" }}
                  exit={{ opacity: 0, filter: "blur(8px)" }}
                  transition={{ duration: 0.25 }}
                >
                  {showDetails ? cardData.expiry : "••/••"}
                </motion.p>
              </AnimatePresence>
            </div>
            <div className="bg-secondary rounded-xl p-4">
              <p className="text-xs text-muted-foreground mb-1">{t("card.cvv")}</p>
              <AnimatePresence mode="wait">
                <motion.p 
                  key={showDetails ? "cvv-visible" : "cvv-hidden"}
                  className="text-base font-mono"
                  initial={{ opacity: 0, filter: "blur(8px)" }}
                  animate={{ opacity: 1, filter: "blur(0px)" }}
                  exit={{ opacity: 0, filter: "blur(8px)" }}
                  transition={{ duration: 0.25 }}
                >
                  {showDetails ? cardData.cvv : "•••"}
                </motion.p>
              </AnimatePresence>
            </div>
          </div>
        </motion.div>

        {/* Billing Address */}
        <Collapsible open={billingOpen} onOpenChange={setBillingOpen}>
          <CollapsibleTrigger className="w-full bg-secondary rounded-xl p-4 flex items-center justify-between">
            <span className="text-sm font-medium">{t("card.billingAddress")}</span>
            {billingOpen ? (
              <ChevronUp className="w-4 h-4 text-muted-foreground" />
            ) : (
              <ChevronDown className="w-4 h-4 text-muted-foreground" />
            )}
          </CollapsibleTrigger>
          <CollapsibleContent className="bg-secondary rounded-b-xl px-4 pb-4 -mt-2 pt-2">
            <p className="text-sm text-muted-foreground">
              123 Main Street, Apt 4B<br />
              New York, NY 10001<br />
              United States
            </p>
          </CollapsibleContent>
        </Collapsible>

        {/* Action Buttons */}
        <motion.div 
          className="grid grid-cols-2 gap-3 pt-2"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.3 }}
        >
          <Button 
            variant="outline" 
            className="h-12 rounded-xl gap-2 bg-secondary border-none hover:bg-muted"
          >
            <Lock className="w-4 h-4" />
            {t("card.lockCard")}
          </Button>
          <Button 
            variant="outline"
            className="h-12 rounded-xl gap-2 bg-secondary border-none hover:bg-muted"
          >
            <RefreshCw className="w-4 h-4" />
            {t("card.replaceCard")}
          </Button>
        </motion.div>

        {/* Balance Section */}
        <motion.div 
          className="bg-secondary rounded-xl p-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.35 }}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground mb-1">{t("card.cardBalance")}</p>
              <AnimatePresence mode="wait">
                <motion.p 
                  key={balanceVisible ? "visible" : "hidden"}
                  className="text-2xl font-bold"
                  initial={{ opacity: 0, filter: "blur(8px)" }}
                  animate={{ opacity: 1, filter: "blur(0px)" }}
                  exit={{ opacity: 0, filter: "blur(8px)" }}
                  transition={{ duration: 0.25 }}
                >
                  {balanceVisible ? (
                    <><AnimatedNumber key={animationKey} value={cardData.balance} /> AED</>
                  ) : "••••••"}
                </motion.p>
              </AnimatePresence>
            </div>
            <button
              onClick={toggleBalanceVisibility}
              className="p-2 rounded-full hover:bg-muted transition-colors"
            >
              {balanceVisible ? (
                <Eye className="w-5 h-5 text-muted-foreground" />
              ) : (
                <EyeOff className="w-5 h-5 text-muted-foreground" />
              )}
            </button>
          </div>
        </motion.div>

        {/* Transactions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.4 }}
        >
          <h2 className="text-lg font-bold mb-3">{t("card.transactions")}</h2>
          <CardTransactionsList groups={virtualCardTransactions} />
        </motion.div>

        {/* Footer */}
        <div className="pt-4 pb-8">
          <PoweredByFooter />
        </div>
      </motion.div>
    </MobileLayout>
  );
};

export default VirtualCard;
