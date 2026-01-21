import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Settings } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { MobileLayout } from "@/components/layout/MobileLayout";
import apofizLogo from "@/assets/apofiz-logo.svg";
import { BalanceCard } from "@/components/dashboard/BalanceCard";
import { ActionButtons } from "@/components/dashboard/ActionButtons";
import { VerifyIdentityCard } from "@/components/dashboard/VerifyIdentityCard";
import { CardsList } from "@/components/dashboard/CardsList";
import { SendToCardButton } from "@/components/dashboard/SendToCardButton";
import { LanguageSwitcher } from "@/components/dashboard/LanguageSwitcher";

import { CardTransactionsList } from "@/components/card/CardTransactionsList";
import { TopUpDrawer } from "@/components/dashboard/TopUpDrawer";
import { SendDrawer } from "@/components/dashboard/SendDrawer";

const mockCards = [
  { id: "1", type: "virtual" as const, name: "Visa Virtual", isActive: true, balance: 213757.49 },
  { id: "2", type: "metal" as const, name: "Visa Metal", isActive: true, balance: 256508.98 },
];

const transactionGroups = [
  {
    date: "January 12",
    totalSpend: 350.00,
    transactions: [
      { id: "19", merchant: "Card Transfer", time: "16:45", amountUSDT: 50.00, amountLocal: 50.00, localCurrency: "AED", color: "#22C55E", type: "card_transfer" as const, senderName: "ANNA JOHNSON", senderCard: "8834", status: "settled" as const },
      { id: "17", merchant: "Card Transfer", time: "15:30", amountUSDT: 250.00, amountLocal: 250.00, localCurrency: "AED", color: "#007AFF", type: "card_transfer" as const, recipientCard: "4521", status: "processing" as const },
      { id: "18", merchant: "Card Transfer", time: "12:15", amountUSDT: 100.00, amountLocal: 100.00, localCurrency: "AED", color: "#007AFF", type: "card_transfer" as const, recipientCard: "8834", status: "settled" as const },
    ],
  },
  {
    date: "January 10",
    totalSpend: 89.19,
    transactions: [
      { id: "1", merchant: "LIFE", time: "13:02", amountUSDT: 8.34, amountLocal: 29.87, localCurrency: "AED", color: "#3B82F6" },
      { id: "2", merchant: "ALAYA", time: "00:59", amountUSDT: 26.80, amountLocal: 96.00, localCurrency: "AED", color: "#22C55E" },
      { id: "3", merchant: "Ongaku", time: "00:17", amountUSDT: 54.05, amountLocal: 193.60, localCurrency: "AED", color: "#F97316" },
    ],
  },
  {
    date: "January 02",
    totalSpend: 62.82,
    transactions: [
      { id: "4", merchant: "OPERA", time: "20:20", amountUSDT: 62.82, amountLocal: 225.00, localCurrency: "AED", color: "#A855F7" },
    ],
  },
  {
    date: "December 31",
    totalSpend: 22.06,
    transactions: [
      { id: "5", merchant: "CELLAR", time: "20:48", amountUSDT: 22.06, amountLocal: 79.00, localCurrency: "AED", color: "#EAB308" },
      { id: "6", merchant: "Top up", time: "20:46", amountUSDT: 194.10, amountLocal: 200.00, localCurrency: "USDT", color: "#22C55E", type: "topup" as const },
    ],
  },
  {
    date: "December 30",
    totalSpend: 678.58,
    transactions: [
      { id: "7", merchant: "BHPC", time: "20:16", amountUSDT: 125.64, amountLocal: 450.00, localCurrency: "AED", color: "#EAB308" },
      { id: "8", merchant: "Bhpc", time: "20:15", amountUSDT: 142.90, amountLocal: 140.78, localCurrency: "$", color: "#EC4899", type: "declined" as const },
      { id: "9", merchant: "Bhpc", time: "20:14", amountUSDT: 157.49, amountLocal: 155.16, localCurrency: "$", color: "#EC4899", type: "declined" as const },
      { id: "10", merchant: "CELLAR", time: "19:53", amountUSDT: 116.54, amountLocal: 114.81, localCurrency: "$", color: "#22C55E" },
      { id: "11", merchant: "Service CEO", time: "07:58", amountUSDT: 11.59, amountLocal: 41.50, localCurrency: "AED", color: "#06B6D4" },
      { id: "12", merchant: "RESTAURANT", time: "03:21", amountUSDT: 424.81, amountLocal: 418.53, localCurrency: "AED", color: "#EF4444" },
      { id: "13", merchant: "Top up", time: "02:30", amountUSDT: 494.10, amountLocal: 500.00, localCurrency: "USDT", color: "#22C55E", type: "topup" as const },
    ],
  },
  {
    date: "December 29",
    totalSpend: 67.01,
    transactions: [
      { id: "14", merchant: "LOGS", time: "23:27", amountUSDT: 67.01, amountLocal: 240.00, localCurrency: "AED", color: "#3B82F6" },
    ],
  },
  {
    date: "December 21",
    totalSpend: 5.00,
    transactions: [
      { id: "15", merchant: "Annual Card fee", time: "23:31", amountUSDT: 183.50, amountLocal: 183.50, localCurrency: "AED", color: "#CCFF00", type: "card_activation" as const },
      { id: "16", merchant: "Top up", time: "23:30", amountUSDT: 44.10, amountLocal: 50.00, localCurrency: "USDT", color: "#22C55E", type: "topup" as const },
    ],
  },
];

const Dashboard = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [topUpOpen, setTopUpOpen] = useState(false);
  const [sendOpen, setSendOpen] = useState(false);

  return (
    <>
      <MobileLayout
        header={
          <p className="text-xs text-muted-foreground flex items-center gap-1">
            {t('dashboard.poweredBy')}{" "}
            <img src={apofizLogo} alt="Apofiz" className="w-4 h-4 inline-block" />{" "}
            <span className="font-semibold text-foreground">Apofiz</span>
          </p>
        }
        rightAction={
          <div className="flex items-center gap-2">
            <LanguageSwitcher />
            <button 
              onClick={() => navigate("/settings")}
              className="relative"
            >
              <Avatar className="w-10 h-10">
                <AvatarImage src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop&crop=face" alt="User" />
                <AvatarFallback>U</AvatarFallback>
              </Avatar>
              <div className="absolute -bottom-0.5 -right-0.5 w-5 h-5 rounded-full bg-secondary flex items-center justify-center border-2 border-background">
                <Settings className="w-3 h-3 text-foreground" />
              </div>
            </button>
          </div>
        }
      >
      <div className="px-4 py-6 space-y-6 pb-28">
        {/* Balance */}
        <BalanceCard balance={470266.47} />

        {/* Action Buttons */}
        <ActionButtons onTopUp={() => setTopUpOpen(true)} onSend={() => setSendOpen(true)} />

        {/* Verify Identity Card */}
        <VerifyIdentityCard progress={0} totalSteps={3} />

        {/* Cards */}
        <CardsList cards={mockCards} />

        {/* Send to Card */}
        <SendToCardButton />

        {/* Transactions */}
        <div>
          <h2 className="text-xl font-bold mb-4">{t('dashboard.transactions')}</h2>
          <CardTransactionsList groups={transactionGroups} />
        </div>

      </div>
    </MobileLayout>

    <TopUpDrawer open={topUpOpen} onOpenChange={setTopUpOpen} />
    <SendDrawer open={sendOpen} onOpenChange={setSendOpen} />
  </>
);
};

export default Dashboard;
