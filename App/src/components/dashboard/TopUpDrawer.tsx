import { useNavigate } from "react-router-dom";
import { ChevronRight, QrCode, Landmark, X } from "lucide-react";
import { useTranslation } from "react-i18next";
import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerClose,
} from "@/components/ui/drawer";

interface TopUpDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const TopUpDrawer = ({ open, onOpenChange }: TopUpDrawerProps) => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  
  const options = [
    {
      id: "stablecoins",
      icon: QrCode,
      title: t("drawer.stablecoins"),
      subtitle: "USDT, USDC",
      iconBg: "bg-primary",
    },
    {
      id: "bank",
      icon: Landmark,
      title: t("drawer.bankTransfer"),
      subtitle: "AED WIRE",
      iconBg: "bg-purple-500",
    },
  ];

  return (
    <Drawer open={open} onOpenChange={onOpenChange}>
      <DrawerContent className="bg-background">
        <DrawerHeader className="relative flex items-center justify-center border-b border-border">
          <DrawerTitle className="text-center text-lg font-semibold">
            {t("drawer.addMoneyWith")}
          </DrawerTitle>
          <DrawerClose className="absolute right-4 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
            <X className="w-4 h-4 text-muted-foreground" />
          </DrawerClose>
        </DrawerHeader>
        <div className="px-4 pb-8 space-y-3">
          {options.map((option) => (
            <button
              key={option.id}
            onClick={() => {
              onOpenChange(false);
              if (option.id === "stablecoins") {
                navigate("/top-up/crypto");
              } else if (option.id === "bank") {
                navigate("/top-up/bank");
              }
            }}
              className="w-full flex items-center gap-4 p-4 bg-muted rounded-2xl hover:bg-muted/80 transition-colors"
            >
              <div className={`w-12 h-12 rounded-full ${option.iconBg} flex items-center justify-center`}>
                <option.icon className="w-6 h-6 text-primary-foreground" />
              </div>
              <div className="flex-1 text-left">
                <p className="font-semibold text-foreground">{option.title}</p>
                <p className="text-sm text-muted-foreground">{option.subtitle}</p>
              </div>
              <ChevronRight className="w-5 h-5 text-muted-foreground" />
            </button>
          ))}
        </div>
      </DrawerContent>
    </Drawer>
  );
};
