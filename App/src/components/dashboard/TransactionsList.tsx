import { ArrowDownLeft, ArrowUpRight, CreditCard, Repeat } from "lucide-react";

interface Transaction {
  id: string;
  type: "incoming" | "outgoing" | "exchange" | "card";
  title: string;
  subtitle?: string;
  amount: number;
  currency: string;
  date: string;
}

interface TransactionsListProps {
  transactions: Transaction[];
  onTransactionClick?: (transaction: Transaction) => void;
}

const getTransactionIcon = (type: Transaction["type"]) => {
  switch (type) {
    case "incoming":
      return <ArrowDownLeft className="w-5 h-5 text-success" />;
    case "outgoing":
      return <ArrowUpRight className="w-5 h-5 text-destructive" />;
    case "exchange":
      return <Repeat className="w-5 h-5 text-primary" />;
    case "card":
      return <CreditCard className="w-5 h-5 text-muted-foreground" />;
    default:
      return null;
  }
};

export const TransactionsList = ({
  transactions,
  onTransactionClick,
}: TransactionsListProps) => {
  const formatAmount = (amount: number, type: Transaction["type"]) => {
    const prefix = type === "incoming" ? "+" : type === "outgoing" ? "-" : "";
    return `${prefix}${Math.abs(amount).toFixed(2)}`;
  };

  if (transactions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4">
        <div className="w-20 h-20 rounded-full bg-secondary flex items-center justify-center mb-4">
          <CreditCard className="w-10 h-10 text-muted-foreground" />
        </div>
        <p className="text-muted-foreground text-center">
          No transactions yet
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {transactions.map((transaction) => (
        <button
          key={transaction.id}
          onClick={() => onTransactionClick?.(transaction)}
          className="w-full flex items-center justify-between p-3 rounded-xl hover:bg-secondary/50 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center">
              {getTransactionIcon(transaction.type)}
            </div>
            <div className="text-left">
              <p className="font-medium">{transaction.title}</p>
              {transaction.subtitle && (
                <p className="text-sm text-muted-foreground">
                  {transaction.subtitle}
                </p>
              )}
            </div>
          </div>
          <div className="text-right">
            <p
              className={`font-semibold ${
                transaction.type === "incoming"
                  ? "text-success"
                  : transaction.type === "outgoing"
                  ? "text-destructive"
                  : ""
              }`}
            >
              {formatAmount(transaction.amount, transaction.type)}{" "}
              {transaction.currency}
            </p>
            <p className="text-xs text-muted-foreground">{transaction.date}</p>
          </div>
        </button>
      ))}
    </div>
  );
};
