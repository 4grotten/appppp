import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronLeft, ChevronDown, Check, CreditCard, ClipboardPaste } from "lucide-react";
import { useTranslation } from "react-i18next";
import { MobileLayout } from "@/components/layout/MobileLayout";
import { PoweredByFooter } from "@/components/layout/PoweredByFooter";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
} from "@/components/ui/drawer";
import { USDT_TO_AED_SEND, AED_TO_USDT_RATE, NETWORK_FEE_PERCENT } from "@/lib/fees";

interface Card {
  id: string;
  type: "virtual" | "metal";
  name: string;
  lastFour: string;
  balance: number;
}

const cards: Card[] = [
  { id: "1", type: "virtual", name: "Visa Virtual", lastFour: "4532", balance: 213757.49 },
  { id: "2", type: "metal", name: "Visa Metal", lastFour: "8901", balance: 256508.98 },
];

const coins = [
  { id: "usdt", name: "Tether", symbol: "USDT", color: "#26A17B" },
  { id: "usdc", name: "USD Coin", symbol: "USDC", color: "#2775CA" },
];

const networksByCoin: Record<string, { id: string; name: string }[]> = {
  usdt: [
    { id: "trc20", name: "Tron (TRC20)" },
    { id: "erc20", name: "Ethereum (ERC20)" },
    { id: "bep20", name: "BNB Chain (BEP20)" },
    { id: "polygon", name: "Polygon" },
  ],
  usdc: [
    { id: "erc20", name: "Ethereum (ERC20)" },
    { id: "bep20", name: "BNB Chain (BEP20)" },
    { id: "polygon", name: "Polygon" },
    { id: "sol", name: "Solana" },
  ],
};

const SendCrypto = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [selectedCard, setSelectedCard] = useState<Card>(cards[0]);
  const [selectedCoin, setSelectedCoin] = useState(coins[0]);
  const [selectedNetwork, setSelectedNetwork] = useState(networksByCoin[coins[0].id][0]);
  const [cardDrawerOpen, setCardDrawerOpen] = useState(false);
  const [coinDrawerOpen, setCoinDrawerOpen] = useState(false);
  const [networkDrawerOpen, setNetworkDrawerOpen] = useState(false);
  const [walletAddress, setWalletAddress] = useState("");
  const [amountAED, setAmountAED] = useState("");

  const amountCrypto = amountAED ? (parseFloat(amountAED) * AED_TO_USDT_RATE).toFixed(2) : "0.00";
  const networkFee = amountAED ? (parseFloat(amountCrypto) * NETWORK_FEE_PERCENT / 100).toFixed(2) : "0.00";
  const amountAfterFee = amountAED ? (parseFloat(amountCrypto) - parseFloat(networkFee)).toFixed(2) : "0.00";
  const isValid = walletAddress.length >= 20 && parseFloat(amountAED) > 0 && parseFloat(amountAED) <= selectedCard.balance;

  const formatAmountInput = (value: string) => {
    const cleaned = value.replace(/[^\d.]/g, "");
    const parts = cleaned.split(".");
    if (parts.length > 2) return amountAED;
    if (parts[1] && parts[1].length > 2) {
      return `${parts[0]}.${parts[1].slice(0, 2)}`;
    }
    return cleaned;
  };

  const formatDisplayAmount = (value: string) => {
    if (!value) return "";
    const num = parseFloat(value);
    if (isNaN(num)) return value;
    const parts = value.split(".");
    const integerPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    if (parts.length > 1) {
      return `${integerPart}.${parts[1]}`;
    }
    return integerPart;
  };

  const parseDisplayAmount = (value: string) => {
    return value.replace(/,/g, "");
  };

  const handleCoinSelect = (coin: typeof coins[0]) => {
    setSelectedCoin(coin);
    setSelectedNetwork(networksByCoin[coin.id][0]);
    setCoinDrawerOpen(false);
  };

  const handleSubmit = () => {
    if (!isValid) return;
    navigate("/");
  };

  return (
    <>
      <MobileLayout
        header={
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors"
          >
            <ChevronLeft className="w-5 h-5" />
            <span className="text-sm">{t("send.back")}</span>
          </button>
        }
      >
        <div className="px-4 py-6 pb-32 space-y-6">
          <div>
            <h1 className="text-2xl font-bold">{t("send.sendToStablecoins")}</h1>
            <p className="text-muted-foreground text-sm mt-1">
              {t("send.withdrawToWallet")}
            </p>
          </div>

          {/* Card Selection */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-muted-foreground">
              {t("send.fromCard")}
            </label>
            <button
              onClick={() => setCardDrawerOpen(true)}
              className="w-full flex items-center justify-between p-4 bg-secondary rounded-2xl hover:bg-muted/80 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  selectedCard.type === "metal" 
                    ? "bg-gradient-to-br from-zinc-400 to-zinc-600" 
                    : "bg-primary"
                }`}>
                  <CreditCard className="w-5 h-5 text-primary-foreground" />
                </div>
                <div className="text-left">
                  <p className="font-semibold">{selectedCard.name}</p>
                  <p className="text-sm text-muted-foreground">
                    •••• {selectedCard.lastFour}
                  </p>
                </div>
              </div>
              <ChevronDown className="w-5 h-5 text-muted-foreground" />
            </button>
          </div>

          {/* Coin Selection */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-muted-foreground">
              {t("send.coin")}
            </label>
            <button
              onClick={() => setCoinDrawerOpen(true)}
              className="w-full flex items-center justify-between p-4 bg-secondary rounded-2xl hover:bg-muted/80 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div 
                  className="w-10 h-10 rounded-full flex items-center justify-center"
                  style={{ backgroundColor: selectedCoin.color }}
                >
                  <span className="text-white font-bold text-sm">
                    {selectedCoin.symbol.charAt(0)}
                  </span>
                </div>
                <div className="text-left">
                  <p className="font-semibold">{selectedCoin.symbol}</p>
                  <p className="text-sm text-muted-foreground">
                    {selectedCoin.name}
                  </p>
                </div>
              </div>
              <ChevronDown className="w-5 h-5 text-muted-foreground" />
            </button>
          </div>

          {/* Network Selection */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-muted-foreground">
              {t("send.network")}
            </label>
            <button
              onClick={() => setNetworkDrawerOpen(true)}
              className="w-full flex items-center justify-between p-4 bg-secondary rounded-2xl hover:bg-muted/80 transition-colors"
            >
              <div className="text-left">
                <p className="font-semibold">{selectedNetwork.name}</p>
              </div>
              <ChevronDown className="w-5 h-5 text-muted-foreground" />
            </button>
          </div>

          {/* Wallet Address */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-muted-foreground">
              {t("send.walletAddress")}
            </label>
            <div className="relative">
              <Input
                value={walletAddress}
                onChange={(e) => setWalletAddress(e.target.value)}
                placeholder={t("send.enterWalletAddress")}
                className="h-14 rounded-2xl bg-secondary border-0 text-base pr-12"
              />
              <button
                type="button"
                onClick={async () => {
                  try {
                    const text = await navigator.clipboard.readText();
                    setWalletAddress(text.trim());
                  } catch (err) {
                    console.error("Failed to read clipboard");
                  }
                }}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-lg hover:bg-background/50 transition-colors"
                aria-label="Paste from clipboard"
              >
                <ClipboardPaste className="w-5 h-5 text-muted-foreground" />
              </button>
            </div>
          </div>

          {/* Amount Input */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-muted-foreground">
                {t("send.amount")}
              </label>
              <span className="text-sm text-muted-foreground">
                {t("send.available")}: <span className="font-medium text-foreground">{selectedCard.balance.toLocaleString('en-US', { minimumFractionDigits: 2 })} AED</span>
              </span>
            </div>
            <div className="relative">
              <Input
                value={formatDisplayAmount(amountAED)}
                onChange={(e) => setAmountAED(formatAmountInput(parseDisplayAmount(e.target.value)))}
                placeholder="0.00"
                className="h-14 rounded-2xl bg-secondary border-0 text-base pr-28"
                inputMode="decimal"
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
                <button
                  onClick={() => setAmountAED(selectedCard.balance.toFixed(2))}
                  className="px-3 py-1.5 rounded-xl bg-primary/10 text-primary text-xs font-bold hover:bg-primary/20 transition-colors"
                >
                  MAX
                </button>
                <span className="text-muted-foreground font-medium">
                  AED
                </span>
              </div>
            </div>
          </div>

          {/* Conversion Display */}
          <div className="bg-secondary rounded-2xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">{t("send.amount")}</span>
              <span className="font-medium">
                {amountCrypto} {selectedCoin.symbol}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">{t("send.networkFee")} ({NETWORK_FEE_PERCENT}%)</span>
              <span className="font-medium text-[#FFA000]">-{networkFee} {selectedCoin.symbol}</span>
            </div>
            <div className="flex items-center justify-between pt-2 border-t border-border">
              <span className="text-muted-foreground">{t("send.youWillReceive")}</span>
              <span className="font-semibold text-lg">
                {amountAfterFee} {selectedCoin.symbol}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">{t("send.exchangeRate")}</span>
              <span className="font-medium">1 USDT = {USDT_TO_AED_SEND.toFixed(2)} AED</span>
            </div>
          </div>

          {/* Warning */}
          <div className="bg-[#FFA000]/10 rounded-2xl p-4">
            <p className="text-sm text-[#FFA000]">
              ⚠️ {t("send.cryptoWarning")}
            </p>
          </div>

          <div className="pt-4">
            <PoweredByFooter />
          </div>
        </div>

        {/* Fixed Submit Button */}
        <div className="fixed bottom-0 left-0 right-0 p-6 max-w-[800px] mx-auto">
          <Button
            onClick={handleSubmit}
            disabled={!isValid}
            className="w-full h-14 rounded-2xl text-base font-semibold bg-primary/90 hover:bg-primary active:scale-95 backdrop-blur-2xl border-2 border-white/50 shadow-lg transition-all"
          >
            Send {amountAfterFee} {selectedCoin.symbol}
          </Button>
        </div>
      </MobileLayout>

      {/* Card Selection Drawer */}
      <Drawer open={cardDrawerOpen} onOpenChange={setCardDrawerOpen}>
        <DrawerContent className="bg-background">
          <DrawerHeader className="pb-2">
            <DrawerTitle className="text-xl font-semibold text-center">
              {t("send.selectCard")}
            </DrawerTitle>
          </DrawerHeader>
          <div className="px-4 pb-8 space-y-3">
            {cards.map((card) => (
              <button
                key={card.id}
                onClick={() => {
                  setSelectedCard(card);
                  setCardDrawerOpen(false);
                }}
                className="w-full flex items-center gap-4 p-4 bg-muted rounded-2xl hover:bg-muted/80 transition-colors"
              >
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                  card.type === "metal" 
                    ? "bg-gradient-to-br from-zinc-400 to-zinc-600" 
                    : "bg-primary"
                }`}>
                  <CreditCard className="w-6 h-6 text-primary-foreground" />
                </div>
                <div className="flex-1 text-left">
                  <p className="font-semibold text-foreground">{card.name}</p>
                  <p className="text-sm text-muted-foreground">
                    •••• {card.lastFour} · {card.balance.toLocaleString('en-US', { minimumFractionDigits: 2 })} AED
                  </p>
                </div>
                {selectedCard.id === card.id && (
                  <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center">
                    <Check className="w-4 h-4 text-primary-foreground" />
                  </div>
                )}
              </button>
            ))}
          </div>
        </DrawerContent>
      </Drawer>

      {/* Coin Selection Drawer */}
      <Drawer open={coinDrawerOpen} onOpenChange={setCoinDrawerOpen}>
        <DrawerContent className="bg-background">
          <DrawerHeader className="pb-2">
            <DrawerTitle className="text-xl font-semibold text-center">
              {t("send.selectCoin")}
            </DrawerTitle>
          </DrawerHeader>
          <div className="px-4 pb-8 space-y-2">
            {coins.map((coin) => (
              <button
                key={coin.id}
                onClick={() => handleCoinSelect(coin)}
                className={`w-full flex items-center justify-between p-4 rounded-2xl transition-colors ${
                  selectedCoin.id === coin.id
                    ? "bg-primary/10 border border-primary"
                    : "bg-muted hover:bg-muted/80"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div 
                    className="w-10 h-10 rounded-full flex items-center justify-center"
                    style={{ backgroundColor: coin.color }}
                  >
                    <span className="text-white font-bold text-sm">
                      {coin.symbol.charAt(0)}
                    </span>
                  </div>
                  <div className="text-left">
                    <p className="font-semibold">{coin.symbol}</p>
                    <p className="text-sm text-muted-foreground">
                      {coin.name}
                    </p>
                  </div>
                </div>
                {selectedCoin.id === coin.id && (
                  <Check className="w-5 h-5 text-primary" />
                )}
              </button>
            ))}
          </div>
        </DrawerContent>
      </Drawer>

      {/* Network Selection Drawer */}
      <Drawer open={networkDrawerOpen} onOpenChange={setNetworkDrawerOpen}>
        <DrawerContent className="bg-background">
          <DrawerHeader className="pb-2">
            <DrawerTitle className="text-xl font-semibold text-center">
              {t("send.selectNetwork")}
            </DrawerTitle>
          </DrawerHeader>
          <div className="px-4 pb-8 space-y-2">
            {networksByCoin[selectedCoin.id].map((network) => (
              <button
                key={network.id}
                onClick={() => {
                  setSelectedNetwork(network);
                  setNetworkDrawerOpen(false);
                }}
                className={`w-full flex items-center justify-between p-4 rounded-2xl transition-colors ${
                  selectedNetwork.id === network.id
                    ? "bg-primary/10 border border-primary"
                    : "bg-muted hover:bg-muted/80"
                }`}
              >
                <p className="font-semibold">{network.name}</p>
                {selectedNetwork.id === network.id && (
                  <Check className="w-5 h-5 text-primary" />
                )}
              </button>
            ))}
          </div>
        </DrawerContent>
      </Drawer>
    </>
  );
};

export default SendCrypto;
