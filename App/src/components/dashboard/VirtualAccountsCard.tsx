import { Building2, ChevronRight } from "lucide-react";

interface VirtualAccountsCardProps {
  isOpened?: boolean;
  onClick?: () => void;
}

export const VirtualAccountsCard = ({
  isOpened = false,
  onClick,
}: VirtualAccountsCardProps) => {
  return (
    <button
      onClick={onClick}
      className="w-full karta-card flex items-center justify-between group"
    >
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center">
          <Building2 className="w-5 h-5 text-primary-foreground" />
        </div>
        <div className="text-left">
          <p className="font-medium">Virtual accounts</p>
          <p className="text-sm text-muted-foreground">
            {isOpened ? "Manage your accounts" : "Not Opened"}
          </p>
        </div>
      </div>
      <ChevronRight className="w-5 h-5 text-muted-foreground group-hover:translate-x-1 transition-transform" />
    </button>
  );
};
