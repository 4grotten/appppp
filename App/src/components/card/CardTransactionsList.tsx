import { useNavigate } from "react-router-dom";
import { Plus, Ban, ArrowUpRight, Clock, CheckCircle } from "lucide-react";
import { useTranslation } from "react-i18next";

interface CardTransaction {
  id: string;
  merchant: string;
  time: string;
  amountUSDT: number;
  amountLocal: number;
  localCurrency: string;
  color: string;
  type?: "payment" | "topup" | "declined" | "card_activation" | "card_transfer";
  recipientCard?: string;
  senderName?: string;
  senderCard?: string;
  status?: "settled" | "pending" | "failed" | "processing";
}

interface TransactionGroup {
  date: string;
  totalSpend: number;
  transactions: CardTransaction[];
}

interface CardTransactionsListProps {
  groups: TransactionGroup[];
  onTransactionClick?: (transaction: CardTransaction) => void;
}

const getInitial = (name: string) => name.charAt(0).toUpperCase();

const translateDate = (date: string, t: (key: string) => string): string => {
  const monthsMap: { [key: string]: string } = {
    "January": "transactions.months.january",
    "February": "transactions.months.february",
    "March": "transactions.months.march",
    "April": "transactions.months.april",
    "May": "transactions.months.may",
    "June": "transactions.months.june",
    "July": "transactions.months.july",
    "August": "transactions.months.august",
    "September": "transactions.months.september",
    "October": "transactions.months.october",
    "November": "transactions.months.november",
    "December": "transactions.months.december",
  };
  
  for (const [month, key] of Object.entries(monthsMap)) {
    if (date.includes(month)) {
      return date.replace(month, t(key));
    }
  }
  return date;
};

const translateMerchant = (merchant: string, t: (key: string) => string): string => {
  const merchantsMap: { [key: string]: string } = {
    "Card Transfer": "transactions.cardTransfer",
    "Top up": "transactions.topUp",
    "Annual Card fee": "transactions.annualCardFee",
  };
  
  return merchantsMap[merchant] ? t(merchantsMap[merchant]) : merchant;
};

export const CardTransactionsList = ({
  groups,
  onTransactionClick,
}: CardTransactionsListProps) => {
  const navigate = useNavigate();
  const { t } = useTranslation();

  const handleClick = (transaction: CardTransaction) => {
    if (onTransactionClick) {
      onTransactionClick(transaction);
    } else {
      navigate(`/transaction/${transaction.id}`);
    }
  };

  if (groups.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4">
        <div className="w-16 h-16 rounded-full bg-secondary flex items-center justify-center mb-3">
          <span className="text-2xl text-muted-foreground">💳</span>
        </div>
        <p className="text-muted-foreground text-center text-sm">
          {t("transactions.noTransactions")}
        </p>
      </div>
    );
  }

  const formatAmount = (transaction: CardTransaction) => {
    const isTopup = transaction.type === "topup";
    const isDeclined = transaction.type === "declined";
    const isCardActivation = transaction.type === "card_activation";
    const isCardTransfer = transaction.type === "card_transfer";
    const isIncomingTransfer = isCardTransfer && transaction.senderCard;
    const isOutgoingTransfer = isCardTransfer && transaction.recipientCard;
    const isProcessing = transaction.status === "processing";
    const prefix = isTopup || isIncomingTransfer ? "+" : isOutgoingTransfer ? "-" : "";
    
    let colorClass = "";
    if (isProcessing && isCardTransfer) {
      colorClass = "text-[#FFA000]";
    } else if (isTopup || isIncomingTransfer) {
      colorClass = "text-green-500";
    } else if (isDeclined) {
      colorClass = "text-red-500";
    } else if (isOutgoingTransfer) {
      colorClass = "text-[#007AFF]";
    }
    
    return { prefix, colorClass, isCardActivation, isCardTransfer, isIncomingTransfer, isOutgoingTransfer };
  };

  return (
    <div className="space-y-4">
      {groups.map((group, groupIndex) => (
        <div 
          key={groupIndex} 
          className="space-y-2"
        >
          {/* Date Header */}
          <div className="flex items-center gap-2">
            <span className="font-semibold text-base">{translateDate(group.date, t)}</span>
            <span className="text-muted-foreground text-sm">
              {t("transactions.spend")} {group.totalSpend.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} AED
            </span>
          </div>

          {/* Transactions */}
          <div className="bg-secondary rounded-2xl overflow-hidden">
            {group.transactions.map((transaction, index) => {
              const { prefix, colorClass, isCardActivation, isCardTransfer, isIncomingTransfer, isOutgoingTransfer } = formatAmount(transaction);
              const isTopup = transaction.type === "topup";
              const isDeclined = transaction.type === "declined";

              return (
                <button
                  key={transaction.id}
                  onClick={() => handleClick(transaction)}
                  className={`w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors ${
                    index < group.transactions.length - 1 ? 'border-b border-border/50' : ''
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      {isCardActivation ? (
                        <div 
                          className="w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm"
                          style={{ backgroundColor: "#CCFF00" }}
                        >
                          <span className="text-black text-lg font-black">C</span>
                        </div>
                      ) : isCardTransfer ? (
                        <div 
                          className="w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold text-sm"
                          style={{ backgroundColor: isIncomingTransfer ? "#22C55E" : "#007AFF" }}
                        >
                          <ArrowUpRight className={`w-5 h-5 ${isIncomingTransfer ? "rotate-180" : ""}`} />
                        </div>
                      ) : (
                        <div 
                          className="w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold text-sm"
                          style={{ backgroundColor: transaction.color }}
                        >
                          {isTopup ? <Plus className="w-5 h-5" /> : getInitial(transaction.merchant)}
                        </div>
                      )}
                      {isDeclined && (
                        <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-white rounded-full flex items-center justify-center shadow-[0_2px_8px_rgba(0,0,0,0.15)]">
                          <Ban className="w-3 h-3 text-red-500" />
                        </div>
                      )}
                    </div>
                    <div className="text-left">
                      <p className="font-medium">{translateMerchant(transaction.merchant, t)}</p>
                      <p className="text-sm text-muted-foreground flex items-center gap-1">
                        {isCardTransfer && (transaction.recipientCard || transaction.senderCard) ? (
                          <>
                            <span>
                          {transaction.senderCard 
                            ? `${t("transactions.from")} •••• ${transaction.senderCard}`
                            : `${t("transactions.to")} •••• ${transaction.recipientCard}`
                          }
                        </span>
                        {transaction.status === 'processing' && (
                          <span className="flex items-center gap-0.5 text-[#FFA000] ml-1">
                            <Clock className="w-3 h-3" />
                            <span className="text-xs">{t("transactions.processing")}</span>
                          </span>
                        )}
                        {transaction.status === 'settled' && (
                          <span className="flex items-center gap-0.5 text-green-500 ml-1">
                            <CheckCircle className="w-3 h-3" />
                            <span className="text-xs">{t("transactions.settled")}</span>
                          </span>
                        )}
                      </>
                    ) : (
                          transaction.time
                        )}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`font-semibold ${colorClass}`}>
                      {prefix}{isTopup ? (transaction.amountUSDT * 3.65 * 0.98).toFixed(2) : transaction.amountUSDT.toFixed(2)} AED
                    </p>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
};
