import { useState, useEffect } from "react";
import { CreditCard, Eye, EyeOff } from "lucide-react";
import { useNavigate } from "react-router-dom";

interface Card {
  id: string;
  type: "virtual" | "metal";
  name: string;
  lastFour?: string;
  isActive: boolean;
  balance?: number;
}

interface CardsListProps {
  cards: Card[];
  onCardClick?: (card: Card) => void;
}

const AnimatedNumber = ({ value, duration = 600 }: { value: number; duration?: number }) => {
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

export const CardsList = ({ cards, onCardClick }: CardsListProps) => {
  const navigate = useNavigate();
  const [visibleBalances, setVisibleBalances] = useState<Set<string>>(new Set());
  const [animationKeys, setAnimationKeys] = useState<Record<string, number>>({});

  const handleCardClick = (card: Card) => {
    if (onCardClick) {
      onCardClick(card);
    } else if (card.type === "virtual") {
      navigate("/card/virtual");
    } else if (card.type === "metal") {
      navigate("/card/metal");
    }
  };

  const toggleBalanceVisibility = (e: React.MouseEvent, cardId: string) => {
    e.stopPropagation();
    setVisibleBalances(prev => {
      const newSet = new Set(prev);
      if (newSet.has(cardId)) {
        newSet.delete(cardId);
      } else {
        newSet.add(cardId);
        setAnimationKeys(keys => ({ ...keys, [cardId]: (keys[cardId] || 0) + 1 }));
      }
      return newSet;
    });
  };

  return (
    <div className="grid grid-cols-2 gap-3">
      {cards.map((card) => (
        <button
          key={card.id}
          onClick={() => handleCardClick(card)}
          className={`karta-card relative flex flex-col items-start gap-2 transition-all hover:shadow-md ${
            !card.isActive ? "opacity-50" : ""
          }`}
        >
          {/* Eye icon in top right corner */}
          {card.balance !== undefined && (
            <div
              onClick={(e) => toggleBalanceVisibility(e, card.id)}
              className="absolute top-3 right-3 p-1 rounded-full hover:bg-secondary/50 transition-colors"
            >
              {visibleBalances.has(card.id) ? (
                <Eye className="w-3.5 h-3.5 text-muted-foreground" />
              ) : (
                <EyeOff className="w-3.5 h-3.5 text-muted-foreground" />
              )}
            </div>
          )}

          <div className="w-8 h-8 rounded-lg bg-secondary flex items-center justify-center">
            <CreditCard className="w-4 h-4 text-muted-foreground" />
          </div>
          <div className="text-left w-full">
            <p className="text-xs text-muted-foreground">{card.name}</p>
            {card.balance !== undefined && (
              <p className="text-sm font-semibold">
                {visibleBalances.has(card.id) 
                  ? <><AnimatedNumber key={animationKeys[card.id] || 0} value={card.balance} /> AED</>
                  : "••••••"
                }
              </p>
            )}
            {card.lastFour && (
              <p className="text-xs text-muted-foreground">
                •••• {card.lastFour}
              </p>
            )}
          </div>
        </button>
      ))}
    </div>
  );
};