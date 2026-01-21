import { Gift, Users } from "lucide-react";

interface KaratRewardsCardProps {
  points?: number;
  usdt?: number;
  onClick?: () => void;
}

export const KaratRewardsCard = ({
  points = 0,
  usdt = 0,
  onClick,
}: KaratRewardsCardProps) => {
  return (
    <button
      onClick={onClick}
      className="w-full bg-karta-dark text-karta-white rounded-2xl p-4 flex items-center justify-between group"
    >
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center">
          <Gift className="w-5 h-5 text-primary-foreground" />
        </div>
        <div className="text-left">
          <p className="font-semibold">Karat</p>
          <p className="text-sm text-karta-gray">Invite Friends to Earn</p>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <div className="text-right">
          <p className="font-bold flex items-center gap-1">
            {points} <span className="text-yellow-400">💎</span>
          </p>
          <p className="text-sm text-karta-gray">{usdt.toFixed(2)} AED</p>
        </div>
        <Users className="w-5 h-5 text-muted-foreground" />
      </div>
    </button>
  );
};
