import { Eye, EyeOff } from "lucide-react";
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import aedCurrency from "@/assets/aed-currency.png";

interface BalanceCardProps {
  balance: number;
  currency?: string;
}

const AnimatedNumber = ({ value, duration = 1000 }: { value: number; duration?: number }) => {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let startTime: number | null = null;
    let animationFrame: number;

    const animate = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      
      // Easing function for smooth deceleration
      const easeOut = 1 - Math.pow(1 - progress, 3);
      setDisplayValue(value * easeOut);

      if (progress < 1) {
        animationFrame = requestAnimationFrame(animate);
      }
    };

    animationFrame = requestAnimationFrame(animate);

    return () => cancelAnimationFrame(animationFrame);
  }, [value, duration]);

  const formatBalance = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  return <>{formatBalance(displayValue)}</>;
};

export const BalanceCard = ({ balance, currency = "AED" }: BalanceCardProps) => {
  const [isVisible, setIsVisible] = useState(false);
  const [animationKey, setAnimationKey] = useState(0);

  const handleToggle = () => {
    if (!isVisible) {
      setAnimationKey(prev => prev + 1);
    }
    setIsVisible(!isVisible);
  };

  return (
    <div className="flex items-center justify-between">
      <div>
        <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
          Card Balance ({currency})
        </p>
        <div className="flex items-center gap-3">
          <AnimatePresence mode="wait">
            <motion.span 
              key={isVisible ? "visible" : "hidden"}
              className="text-4xl font-bold tracking-tight flex items-center gap-2"
              initial={{ opacity: 0, filter: "blur(10px)" }}
              animate={{ opacity: 1, filter: "blur(0px)" }}
              exit={{ opacity: 0, filter: "blur(10px)" }}
              transition={{ duration: 0.3, ease: "easeOut" }}
            >
              {isVisible ? (
                <>
                  <img src={aedCurrency} alt="AED" className="w-9 h-9" />
                  <AnimatedNumber key={animationKey} value={balance} duration={800} /> AED
                </>
              ) : "••••••"}
            </motion.span>
          </AnimatePresence>
          <button
            onClick={handleToggle}
            className="p-1.5 rounded-full hover:bg-secondary transition-colors"
            aria-label={isVisible ? "Hide balance" : "Show balance"}
          >
            {isVisible ? (
              <Eye className="w-5 h-5 text-muted-foreground" />
            ) : (
              <EyeOff className="w-5 h-5 text-muted-foreground" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
};