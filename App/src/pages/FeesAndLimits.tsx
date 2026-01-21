import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { MobileLayout } from "@/components/layout/MobileLayout";
import { PoweredByFooter } from "@/components/layout/PoweredByFooter";
import { Receipt, ChevronRight, CreditCard, ArrowDownToLine, Send, ArrowLeftRight, SlidersHorizontal } from "lucide-react";
import { Slider } from "@/components/ui/slider";
import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
} from "@/components/ui/drawer";
import { Button } from "@/components/ui/button";
import {
  VIRTUAL_CARD_ANNUAL_FEE,
  VIRTUAL_CARD_REPLACEMENT_FEE,
  METAL_CARD_ANNUAL_FEE,
  METAL_CARD_REPLACEMENT_FEE,
  VIRTUAL_ACCOUNT_OPENING_FEE,
  USDT_TO_AED_TOP_UP,
  USDT_TO_AED_SEND,
  TOP_UP_CRYPTO_FEE,
  TOP_UP_BANK_FEE_PERCENT,
  CARD_TO_CARD_FEE_PERCENT,
  BANK_TRANSFER_FEE_PERCENT,
  NETWORK_FEE_PERCENT,
  CURRENCY_CONVERSION_FEE_PERCENT,
} from "@/lib/fees";

interface FeeItemProps {
  label: string;
  value: string;
  isLast?: boolean;
}

const FeeItem = ({ label, value, isLast = false }: FeeItemProps) => (
  <div className={`flex items-center justify-between py-3 ${!isLast ? 'border-b border-border' : ''}`}>
    <span className="text-muted-foreground">{label}</span>
    <span className="text-foreground font-medium text-right">{value}</span>
  </div>
);

interface FeeSectionProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}

const FeeSection = ({ title, icon, children }: FeeSectionProps) => (
  <div className="mb-6">
    <div className="flex items-center gap-2 mb-3 px-1">
      <div className="text-primary">{icon}</div>
      <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
        {title}
      </h3>
    </div>
    <div className="bg-card rounded-2xl px-4 border border-border/50 shadow-sm">
      {children}
    </div>
  </div>
);

interface LimitItemProps {
  label: string;
  dailyValue: number;
  perTransactionValue: number;
  onClick: () => void;
  isLast?: boolean;
  dailyLabel: string;
  perTxLabel: string;
}

const formatAmount = (amount: number) => {
  return amount.toLocaleString('en-US') + ' AED';
};

const LimitItem = ({ label, dailyValue, perTransactionValue, onClick, isLast = false, dailyLabel, perTxLabel }: LimitItemProps) => (
  <button 
    onClick={onClick}
    className={`flex items-center justify-between py-3 w-full text-left ${!isLast ? 'border-b border-border' : ''}`}
  >
    <div className="flex flex-col">
      <span className="text-foreground font-medium">{label}</span>
      <span className="text-xs text-muted-foreground">
        {dailyLabel}: {formatAmount(dailyValue)} · {perTxLabel}: {formatAmount(perTransactionValue)}
      </span>
    </div>
    <ChevronRight className="w-5 h-5 text-muted-foreground" />
  </button>
);

interface LimitSliderProps {
  label: string;
  value: number;
  max: number;
  onChange: (value: number) => void;
}

const LimitSlider = ({ label, value, max, onChange }: LimitSliderProps) => (
  <div className="py-4">
    <div className="flex items-center justify-between mb-3">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-foreground font-medium">{formatAmount(value)}</span>
    </div>
    <Slider
      value={[value]}
      onValueChange={(values) => onChange(values[0])}
      max={max}
      min={0}
      step={max === 1000000 ? 10000 : 1000}
      className="w-full"
    />
    <div className="flex justify-between mt-1">
      <span className="text-xs text-muted-foreground">0 AED</span>
      <span className="text-xs text-muted-foreground">{formatAmount(max)}</span>
    </div>
  </div>
);

const FeesAndLimits = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  
  const [transferDrawerOpen, setTransferDrawerOpen] = useState(false);
  const [withdrawalDrawerOpen, setWithdrawalDrawerOpen] = useState(false);
  
  const [transferDailyLimit, setTransferDailyLimit] = useState(500000);
  const [transferPerTransaction, setTransferPerTransaction] = useState(50000);
  const [withdrawalDailyLimit, setWithdrawalDailyLimit] = useState(500000);
  const [withdrawalPerTransaction, setWithdrawalPerTransaction] = useState(50000);

  return (
    <MobileLayout
      showBackButton
      onBack={() => navigate(-1)}
    >
      <div className="flex flex-col items-center pt-8 pb-6">
        <div className="w-20 h-20 mb-4 flex items-center justify-center">
          <Receipt className="w-16 h-16 text-primary/60" strokeWidth={1} />
        </div>
        <h1 className="text-2xl font-bold text-foreground">{t("feesAndLimits.title")}</h1>
      </div>

      <div className="px-4 pb-28">
        {/* One-Time Fees */}
        <FeeSection title={t("feesAndLimits.oneTimeFees")} icon={<CreditCard className="w-4 h-4" />}>
          <FeeItem label={t("feesAndLimits.virtualCardAnnual")} value={`${VIRTUAL_CARD_ANNUAL_FEE.toFixed(2)} AED`} />
          <FeeItem label={t("feesAndLimits.virtualCardReplacement")} value={`${VIRTUAL_CARD_REPLACEMENT_FEE.toFixed(2)} AED`} />
          <FeeItem label={t("feesAndLimits.metalCardAnnual")} value={`${METAL_CARD_ANNUAL_FEE.toFixed(2)} AED`} />
          <FeeItem label={t("feesAndLimits.metalCardReplacement")} value={`${METAL_CARD_REPLACEMENT_FEE.toFixed(2)} AED`} />
          <FeeItem label={t("feesAndLimits.virtualAccountOpening")} value={`${VIRTUAL_ACCOUNT_OPENING_FEE.toFixed(2)} AED`} isLast />
        </FeeSection>

        {/* Top Up */}
        <FeeSection title={t("feesAndLimits.topUp")} icon={<ArrowDownToLine className="w-4 h-4" />}>
          <FeeItem label={t("feesAndLimits.exchangeRate")} value={`1 USDT = ${USDT_TO_AED_TOP_UP.toFixed(2)} AED`} />
          <FeeItem label={t("feesAndLimits.withCrypto")} value={`${TOP_UP_CRYPTO_FEE.toFixed(2)} USDT`} />
          <FeeItem label={t("feesAndLimits.withBankTransfer")} value={`${TOP_UP_BANK_FEE_PERCENT}%`} isLast />
        </FeeSection>

        {/* Send */}
        <FeeSection title={t("feesAndLimits.send")} icon={<Send className="w-4 h-4" />}>
          <FeeItem label={t("feesAndLimits.easyCardToEasyCard")} value={`${CARD_TO_CARD_FEE_PERCENT}%`} />
          <FeeItem label={t("feesAndLimits.toBankAccount")} value={`${BANK_TRANSFER_FEE_PERCENT}%`} />
          <FeeItem label={t("feesAndLimits.networkFee")} value={`${NETWORK_FEE_PERCENT}%`} />
          <FeeItem label={t("feesAndLimits.exchangeRate")} value={`1 USDT = ${USDT_TO_AED_SEND.toFixed(2)} AED`} isLast />
        </FeeSection>

        {/* Transactions */}
        <FeeSection title={t("feesAndLimits.transactionsSection")} icon={<ArrowLeftRight className="w-4 h-4" />}>
          <FeeItem label={t("feesAndLimits.currencyConversion")} value={`${CURRENCY_CONVERSION_FEE_PERCENT.toFixed(2)}%`} isLast />
        </FeeSection>

        {/* Limits Settings */}
        <FeeSection title={t("feesAndLimits.limitsSettings")} icon={<SlidersHorizontal className="w-4 h-4" />}>
          <LimitItem 
            label={t("feesAndLimits.transferLimits")}
            dailyValue={transferDailyLimit}
            perTransactionValue={transferPerTransaction}
            onClick={() => setTransferDrawerOpen(true)}
            dailyLabel={t("feesAndLimits.daily")}
            perTxLabel={t("feesAndLimits.perTx")}
          />
          <LimitItem 
            label={t("feesAndLimits.withdrawalLimits")}
            dailyValue={withdrawalDailyLimit}
            perTransactionValue={withdrawalPerTransaction}
            onClick={() => setWithdrawalDrawerOpen(true)}
            dailyLabel={t("feesAndLimits.daily")}
            perTxLabel={t("feesAndLimits.perTx")}
            isLast
          />
        </FeeSection>

        <PoweredByFooter />
      </div>

      {/* Transfer Limits Drawer */}
      <Drawer open={transferDrawerOpen} onOpenChange={setTransferDrawerOpen}>
        <DrawerContent className="bg-background">
          <DrawerHeader className="pb-2">
            <DrawerTitle className="text-xl font-semibold text-center">
              {t("feesAndLimits.transferLimits")}
            </DrawerTitle>
          </DrawerHeader>
          <div className="px-4 pb-8">
            <LimitSlider 
              label={t("feesAndLimits.dailyLimit")}
              value={transferDailyLimit} 
              max={1000000}
              onChange={setTransferDailyLimit}
            />
            <LimitSlider 
              label={t("feesAndLimits.perTransaction")}
              value={transferPerTransaction} 
              max={100000}
              onChange={setTransferPerTransaction}
            />
            <button 
              onClick={() => setTransferDrawerOpen(false)} 
              className="w-full bg-primary text-white font-semibold py-4 rounded-xl hover:bg-primary/90 transition-all backdrop-blur-2xl border-2 border-white/50 shadow-lg active:scale-95 mt-4"
            >
              {t("feesAndLimits.save")}
            </button>
          </div>
        </DrawerContent>
      </Drawer>

      {/* Withdrawal Limits Drawer */}
      <Drawer open={withdrawalDrawerOpen} onOpenChange={setWithdrawalDrawerOpen}>
        <DrawerContent className="bg-background">
          <DrawerHeader className="pb-2">
            <DrawerTitle className="text-xl font-semibold text-center">
              {t("feesAndLimits.withdrawalLimits")}
            </DrawerTitle>
          </DrawerHeader>
          <div className="px-4 pb-8">
            <LimitSlider 
              label={t("feesAndLimits.dailyLimit")}
              value={withdrawalDailyLimit} 
              max={1000000}
              onChange={setWithdrawalDailyLimit}
            />
            <LimitSlider 
              label={t("feesAndLimits.perTransaction")}
              value={withdrawalPerTransaction} 
              max={100000}
              onChange={setWithdrawalPerTransaction}
            />
            <button 
              onClick={() => setWithdrawalDrawerOpen(false)} 
              className="w-full bg-primary text-white font-semibold py-4 rounded-xl hover:bg-primary/90 transition-all backdrop-blur-2xl border-2 border-white/50 shadow-lg active:scale-95 mt-4"
            >
              {t("feesAndLimits.save")}
            </button>
          </div>
        </DrawerContent>
      </Drawer>
    </MobileLayout>
  );
};

export default FeesAndLimits;
