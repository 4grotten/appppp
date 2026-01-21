import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ChevronLeft, CheckCircle, Info, MessageSquare, Ban, Plus, ExternalLink, ArrowUpRight, Clock, Eye, EyeOff, Copy } from "lucide-react";
import { toast } from "sonner";
import { MobileLayout } from "@/components/layout/MobileLayout";
import { PoweredByFooter } from "@/components/layout/PoweredByFooter";
import { useTranslation } from "react-i18next";

// Mock transaction data - in real app would come from API/state
const mockTransactions: Record<string, {
  id: string;
  merchant: string;
  time: string;
  date: string;
  amountUSDT: number;
  amountLocal: number;
  localCurrency: string;
  color: string;
  cardLast4: string;
  exchangeRate: number;
  status: "settled" | "pending" | "failed" | "processing";
  type?: "payment" | "topup" | "declined" | "card_activation" | "card_transfer";
  fromAddress?: string;
  tokenNetwork?: string;
  kartaFee?: number;
  declineReason?: string;
  cardType?: "Virtual" | "Metal";
  recipientCard?: string;
  recipientCardFull?: string;
  recipientName?: string;
  transferFee?: number;
  fromCardFull?: string;
  senderName?: string;
  senderCard?: string;
  senderCardFull?: string;
  toCardFull?: string;
}> = {
  "1": { id: "1", merchant: "LIFE", time: "01:02 PM", date: "January 10", amountUSDT: 8.34, amountLocal: 29.87, localCurrency: "AED", color: "#3B82F6", cardLast4: "7617", exchangeRate: 3.58, status: "settled", cardType: "Virtual" },
  "2": { id: "2", merchant: "ALAYA", time: "12:59 AM", date: "January 10", amountUSDT: 26.80, amountLocal: 96.00, localCurrency: "AED", color: "#22C55E", cardLast4: "7617", exchangeRate: 3.58, status: "settled", cardType: "Virtual" },
  "3": { id: "3", merchant: "Ongaku", time: "12:17 AM", date: "January 10", amountUSDT: 54.05, amountLocal: 193.60, localCurrency: "AED", color: "#F97316", cardLast4: "4521", exchangeRate: 3.58, status: "settled", cardType: "Metal" },
  "4": { id: "4", merchant: "OPERA", time: "08:20 PM", date: "January 02", amountUSDT: 62.82, amountLocal: 225.00, localCurrency: "AED", color: "#A855F7", cardLast4: "4521", exchangeRate: 3.58, status: "settled", cardType: "Metal" },
  "5": { id: "5", merchant: "CELLAR", time: "08:48 PM", date: "December 31", amountUSDT: 22.06, amountLocal: 79.00, localCurrency: "AED", color: "#EAB308", cardLast4: "7617", exchangeRate: 3.58, status: "settled", cardType: "Virtual" },
  "6": { id: "6", merchant: "Top up", time: "08:46 PM", date: "December 31", amountUSDT: 194.10, amountLocal: 200.00, localCurrency: "USDT", color: "#22C55E", cardLast4: "7617", exchangeRate: 1, status: "settled", type: "topup", fromAddress: "TFVFktvwmaEnMVh6ZxZq2rvmLePfTxhX9L", tokenNetwork: "USDT, Tron (TRC20)", kartaFee: 5.90, cardType: "Virtual" },
  "7": { id: "7", merchant: "BHPC", time: "08:16 PM", date: "December 30", amountUSDT: 125.64, amountLocal: 450.00, localCurrency: "AED", color: "#EAB308", cardLast4: "4521", exchangeRate: 3.58, status: "settled", cardType: "Metal" },
  "8": { id: "8", merchant: "Bhpc", time: "08:15 PM", date: "December 30", amountUSDT: 142.90, amountLocal: 140.78, localCurrency: "$", color: "#EC4899", cardLast4: "7617", exchangeRate: 0.99, status: "failed", type: "declined", declineReason: "No funds", cardType: "Virtual" },
  "9": { id: "9", merchant: "Bhpc", time: "08:14 PM", date: "December 30", amountUSDT: 157.49, amountLocal: 155.16, localCurrency: "$", color: "#EC4899", cardLast4: "4521", exchangeRate: 0.99, status: "failed", type: "declined", declineReason: "No funds", cardType: "Metal" },
  "10": { id: "10", merchant: "CELLAR", time: "07:53 PM", date: "December 30", amountUSDT: 116.54, amountLocal: 114.81, localCurrency: "$", color: "#22C55E", cardLast4: "7617", exchangeRate: 0.985, status: "settled", cardType: "Virtual" },
  "11": { id: "11", merchant: "Service CEO", time: "07:58 AM", date: "December 30", amountUSDT: 11.59, amountLocal: 41.50, localCurrency: "AED", color: "#06B6D4", cardLast4: "4521", exchangeRate: 3.58, status: "settled", cardType: "Metal" },
  "12": { id: "12", merchant: "RESTAURANT", time: "03:21 AM", date: "December 30", amountUSDT: 424.81, amountLocal: 418.53, localCurrency: "AED", color: "#EF4444", cardLast4: "7617", exchangeRate: 0.985, status: "settled", cardType: "Virtual" },
  "13": { id: "13", merchant: "Top up", time: "02:30 AM", date: "December 30", amountUSDT: 494.10, amountLocal: 500.00, localCurrency: "USDT", color: "#22C55E", cardLast4: "4521", exchangeRate: 1, status: "settled", type: "topup", fromAddress: "TFVFktvwmaEnMVh6ZxZq2rvmLePfTxhX9L", tokenNetwork: "USDT, Tron (TRC20)", kartaFee: 5.90, cardType: "Metal" },
  "14": { id: "14", merchant: "LOGS", time: "11:27 PM", date: "December 29", amountUSDT: 67.01, amountLocal: 240.00, localCurrency: "AED", color: "#3B82F6", cardLast4: "7617", exchangeRate: 3.58, status: "settled", cardType: "Virtual" },
  "15": { id: "15", merchant: "Annual Card fee", time: "11:31 PM", date: "December 21", amountUSDT: 183.50, amountLocal: 183.50, localCurrency: "AED", color: "#CCFF00", cardLast4: "7617", exchangeRate: 1, status: "settled", type: "card_activation", cardType: "Virtual" },
  "16": { id: "16", merchant: "Top up", time: "11:30 PM", date: "December 21", amountUSDT: 44.10, amountLocal: 50.00, localCurrency: "USDT", color: "#22C55E", cardLast4: "7617", exchangeRate: 1, status: "settled", type: "topup", fromAddress: "TFVFktvwmaEnMVh6ZxZq2rvmLePfTxhX9L", tokenNetwork: "USDT, Tron (TRC20)", kartaFee: 5.90, cardType: "Virtual" },
  "17": { id: "17", merchant: "Card Transfer", time: "03:30 PM", date: "January 12", amountUSDT: 250.00, amountLocal: 250.00, localCurrency: "AED", color: "#007AFF", cardLast4: "7617", exchangeRate: 1, status: "processing", type: "card_transfer", recipientCard: "4521", recipientCardFull: "4532 8921 0045 4521", recipientName: "JOHN SMITH", transferFee: 3.75, fromCardFull: "4147 2034 5567 7617", cardType: "Virtual" },
  "18": { id: "18", merchant: "Card Transfer", time: "12:15 PM", date: "January 12", amountUSDT: 100.00, amountLocal: 100.00, localCurrency: "AED", color: "#007AFF", cardLast4: "4521", exchangeRate: 1, status: "settled", type: "card_transfer", recipientCard: "8834", recipientCardFull: "4111 2233 4455 8834", recipientName: "ANNA JOHNSON", transferFee: 1.50, fromCardFull: "4532 8921 0045 4521", cardType: "Metal" },
  "19": { id: "19", merchant: "Card Transfer", time: "04:45 PM", date: "January 12", amountUSDT: 50.00, amountLocal: 50.00, localCurrency: "AED", color: "#22C55E", cardLast4: "7617", exchangeRate: 1, status: "settled", type: "card_transfer", senderName: "ANNA JOHNSON", senderCard: "8834", senderCardFull: "4111 2233 4455 8834", toCardFull: "4147 2034 5567 7617", cardType: "Virtual" },
};

const TransactionDetails = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  
  const transaction = id ? mockTransactions[id] : null;

  if (!transaction) {
    return (
      <MobileLayout
        header={
          <button 
            onClick={() => navigate(-1)}
            className="flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors"
          >
            <ChevronLeft className="w-5 h-5" />
            <span className="text-sm">{t("transaction.back")}</span>
          </button>
        }
      >
        <div className="flex items-center justify-center h-64">
          <p className="text-muted-foreground">{t("transaction.notFound")}</p>
        </div>
      </MobileLayout>
    );
  }

  const getInitial = (name: string) => name.charAt(0).toUpperCase();
  const isTopup = transaction.type === "topup";
  const isDeclined = transaction.type === "declined";
  const isCardActivation = transaction.type === "card_activation";
  const isCardTransfer = transaction.type === "card_transfer";
  const isIncomingTransfer = isCardTransfer && !!transaction.senderCard;
  const isOutgoingTransfer = isCardTransfer && !!transaction.recipientCard;
  
  const [showToCard, setShowToCard] = useState(false);
  const [showFromCard, setShowFromCard] = useState(false);

  return (
    <MobileLayout
      header={
        <button 
          onClick={() => navigate(-1)}
          className="flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors"
        >
          <ChevronLeft className="w-5 h-5" />
          <span className="text-sm">{t("transaction.back")}</span>
        </button>
      }
    >
      <div className="px-4 py-6 space-y-6">
        {/* Header with merchant icon and amount */}
        <div className="flex flex-col items-center text-center space-y-3">
          {isCardActivation ? (
            <div 
              className="w-20 h-20 rounded-full flex items-center justify-center font-black text-4xl"
              style={{ backgroundColor: "#CCFF00" }}
            >
              <span className="text-black">C</span>
            </div>
          ) : isCardTransfer ? (
            <div 
              className="w-20 h-20 rounded-full flex items-center justify-center text-white"
              style={{ backgroundColor: isIncomingTransfer ? "#22C55E" : "#007AFF" }}
            >
              <ArrowUpRight className={`w-10 h-10 ${isIncomingTransfer ? "rotate-180" : ""}`} />
            </div>
          ) : (
            <div 
              className="w-20 h-20 rounded-full flex items-center justify-center text-white font-bold text-3xl"
              style={{ backgroundColor: transaction.color }}
            >
              {isTopup ? <Plus className="w-10 h-10" /> : getInitial(transaction.merchant)}
            </div>
          )}
          
          <div className="space-y-1">
            <p className={`text-4xl font-bold ${isTopup || isIncomingTransfer ? 'text-green-500' : isDeclined ? 'text-red-500' : isOutgoingTransfer ? 'text-[#007AFF]' : ''}`}>
              {isTopup || isIncomingTransfer ? '+' : '-'}{isTopup ? (transaction.amountUSDT * 3.65 * 0.98).toFixed(2) : transaction.amountUSDT.toFixed(2)} <span className="text-xl font-medium text-muted-foreground">AED</span>
            </p>
            <p className="text-base">
              {isTopup ? t('transaction.topUp') : isCardActivation ? t('transaction.annualCardFee') : isIncomingTransfer ? t('transaction.received') : isOutgoingTransfer ? t('transaction.cardTransfer') : t('transaction.paymentTo', { merchant: transaction.merchant })}
            </p>
            <p className="text-sm text-muted-foreground">
              {transaction.date}, {transaction.time}
            </p>
          </div>
        </div>

        {/* Status and Card/Address info */}
        <div className="bg-secondary rounded-2xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">{t("transaction.status")}</span>
            <div className="flex flex-col items-end">
              <div className="flex items-center gap-1.5">
                <span className={`font-medium ${isDeclined ? 'text-red-500' : transaction.status === 'processing' ? 'text-[#FFA000]' : ''}`}>
                  {isDeclined ? t("transaction.declined") : transaction.status === 'processing' ? t("transaction.processing") : t("transaction.settled")}
                </span>
                {isDeclined ? (
                  <Ban className="w-4 h-4 text-red-500" />
                ) : transaction.status === 'processing' ? (
                  <Clock className="w-4 h-4 text-[#FFA000]" />
                ) : (
                  <CheckCircle className="w-4 h-4 text-green-500" />
                )}
              </div>
              {isDeclined && transaction.declineReason && (
                <span className="text-sm text-muted-foreground">
                  {transaction.declineReason === "No funds" ? t("transaction.noFunds") : transaction.declineReason}
                </span>
              )}
            </div>
          </div>
          
          {isTopup ? (
            <>
              <div className="flex items-start justify-between">
                <span className="text-muted-foreground">{t("transaction.fromAddress")}</span>
                <span className="font-medium text-right text-sm max-w-[200px] break-all">{transaction.fromAddress}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">{t("transaction.tokenNetwork")}</span>
                <span className="font-medium">{transaction.tokenNetwork}</span>
              </div>
            </>
          ) : isCardActivation ? (
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">{t("transaction.cardType")}</span>
              <span className="font-medium">Visa {transaction.cardType}</span>
            </div>
          ) : isIncomingTransfer ? (
            <>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">{t("transaction.sender")}</span>
                <span className="font-medium">{transaction.senderName}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">{t("transaction.fromCard")}</span>
                <div className="flex items-center gap-2">
                  <span className="font-medium">
                    {showFromCard ? `Visa ${transaction.senderCardFull}` : `Visa ••${transaction.senderCard}`}
                  </span>
                  <button 
                    onClick={() => {
                      navigator.clipboard.writeText(transaction.senderCardFull?.replace(/\s/g, '') || '');
                      toast.success(t("toast.cardNumberCopied"));
                    }}
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                  <button 
                    onClick={() => setShowFromCard(!showFromCard)}
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {showFromCard ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">{t("transaction.toCard")}</span>
                <div className="flex items-center gap-2">
                  <span className="font-medium">
                    {showToCard ? `Visa Virtual ${transaction.toCardFull}` : `Visa Virtual ••${transaction.cardLast4}`}
                  </span>
                  <button 
                    onClick={() => {
                      navigator.clipboard.writeText(transaction.toCardFull?.replace(/\s/g, '') || '');
                      toast.success(t("toast.cardNumberCopied"));
                    }}
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                  <button 
                    onClick={() => setShowToCard(!showToCard)}
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {showToCard ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            </>
          ) : isOutgoingTransfer ? (
            <>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">{t("transaction.recipient")}</span>
                <span className="font-medium">{transaction.recipientName}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">{t("transaction.toCard")}</span>
                <div className="flex items-center gap-2">
                  <span className="font-medium">
                    {showToCard ? `Visa ${transaction.recipientCardFull}` : `Visa ••${transaction.recipientCard}`}
                  </span>
                  <button 
                    onClick={() => {
                      navigator.clipboard.writeText(transaction.recipientCardFull?.replace(/\s/g, '') || '');
                      toast.success(t("toast.cardNumberCopied"));
                    }}
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                  <button 
                    onClick={() => setShowToCard(!showToCard)}
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {showToCard ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">{t("transaction.fromCard")}</span>
                <div className="flex items-center gap-2">
                  <span className="font-medium">
                    {showFromCard ? `Visa Metal ${transaction.fromCardFull}` : `Visa Metal ••${transaction.cardLast4}`}
                  </span>
                  <button 
                    onClick={() => {
                      navigator.clipboard.writeText(transaction.fromCardFull?.replace(/\s/g, '') || '');
                      toast.success(t("toast.cardNumberCopied"));
                    }}
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                  <button 
                    onClick={() => setShowFromCard(!showFromCard)}
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {showFromCard ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">{t("transaction.card")}</span>
              <span className="font-medium">Visa {transaction.cardType || 'Virtual'} ••{transaction.cardLast4}</span>
            </div>
          )}
        </div>

        {/* Transaction details */}
        <div className="bg-secondary rounded-2xl p-4 space-y-3">
          {isTopup ? (
            <>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">{t("transaction.received")}</span>
                <span className="font-medium">{transaction.amountUSDT.toFixed(2)} USDT</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">{t("transaction.exchangeRate")}</span>
                <span className="font-medium">1 USDT = 3.65 AED</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">{t("transaction.cardFee")}</span>
                <span className="font-medium">2%</span>
              </div>
              <div className="flex items-center justify-between pt-2 border-t border-border">
                <span className="text-muted-foreground">{t("transaction.credited")}</span>
                <span className="font-semibold text-green-500">+{(transaction.amountUSDT * 3.65 * 0.98).toFixed(2)} AED</span>
              </div>
            </>
          ) : isCardActivation ? (
            <>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">{t("transaction.price")}</span>
                <span className="font-medium">50.00 USD</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">{t("transaction.exchangeRate")}</span>
                <span className="font-medium">1 USD = 3.65 AED</span>
              </div>
              <div className="flex items-center justify-between pt-2 border-t border-border">
                <span className="text-muted-foreground">{t("transaction.amount")}</span>
                <span className="font-semibold">182.50 AED</span>
              </div>
            </>
          ) : isIncomingTransfer ? (
            <>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">{t("transaction.receivedAmount")}</span>
                <span className="font-semibold text-green-500">+{transaction.amountLocal.toFixed(2)} AED</span>
              </div>
            </>
          ) : isOutgoingTransfer ? (
            <>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">{t("transaction.transferAmount")}</span>
                <span className="font-medium">{transaction.amountLocal.toFixed(2)} AED</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">{t("transaction.fee")}</span>
                <span className="font-medium">{transaction.transferFee?.toFixed(2)} AED</span>
              </div>
              <div className="flex items-center justify-between pt-2 border-t border-border">
                <span className="text-muted-foreground">{t("transaction.total")}</span>
                <span className="font-semibold">{(transaction.amountUSDT + (transaction.transferFee || 0)).toFixed(2)} AED</span>
              </div>
            </>
          ) : (
            <>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">{t("transaction.amount")}</span>
                <span className="font-semibold">{transaction.amountUSDT.toFixed(2)} AED</span>
              </div>
            </>
          )}
        </div>

        {/* Transaction details link (only for topup) */}
        {isTopup && (
          <div className="bg-secondary rounded-2xl overflow-hidden">
            <button className="w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors">
              <span className="font-medium">{t("transaction.transactionDetails")}</span>
              <ExternalLink className="w-5 h-5 text-muted-foreground" />
            </button>
          </div>
        )}

        {/* Links */}
        <div className="bg-secondary rounded-2xl overflow-hidden">
          <button className="w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors border-b border-border/50">
            <span className="font-medium">{t("transaction.termsAndFees")}</span>
            <Info className="w-5 h-5 text-muted-foreground" />
          </button>
          <button className="w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors">
            <span className="font-medium">{t("transaction.contactSupport")}</span>
            <MessageSquare className="w-5 h-5 text-muted-foreground" />
          </button>
        </div>

        {/* Footer */}
        <div className="pt-4">
          <PoweredByFooter />
        </div>
      </div>
    </MobileLayout>
  );
};

export default TransactionDetails;
