import { useNavigate } from "react-router-dom";
import { Copy, Share2 } from "lucide-react";
import { MobileLayout } from "@/components/layout/MobileLayout";
import { toast } from "sonner";
import { useTranslation } from "react-i18next";
import { TOP_UP_BANK_FEE_PERCENT, TOP_UP_BANK_MIN_AMOUNT } from "@/lib/fees";

interface BankDetail {
  label: string;
  value: string;
}

const TopUpBankDetails = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();

  const bankDetails: BankDetail[] = [
    { label: t("topUp.beneficiary"), value: "Easy Card LLC" },
    { label: t("topUp.accountNumber"), value: "1234567890123" },
    { label: t("topUp.iban"), value: "AE070331234567890123456" },
    { label: t("topUp.bankName"), value: "Emirates NBD" },
    { label: t("topUp.bankAddress"), value: "Dubai, United Arab Emirates" },
  ];

  const feeDetails = [
    { label: t("topUp.topUpFee"), value: `${TOP_UP_BANK_FEE_PERCENT}%` },
    { label: t("topUp.networkFee"), value: "0 AED" },
    { label: t("topUp.minimumAmount"), value: `${TOP_UP_BANK_MIN_AMOUNT} AED` },
    { label: t("topUp.expectedArrival"), value: t("topUp.workingDays") },
  ];

  const handleCopy = (value: string, label: string) => {
    navigator.clipboard.writeText(value);
    toast.success(t("toast.copied", { label }));
  };

  const handleShare = async () => {
    const detailsText = bankDetails
      .map((d) => `${d.label}: ${d.value}`)
      .join("\n");

    const shareData = {
      title: "AED Bank Account Details",
      text: `AED Wire Transfer Details:\n\n${detailsText}`,
    };

    try {
      if (navigator.share) {
        await navigator.share(shareData);
      } else {
        navigator.clipboard.writeText(shareData.text);
        toast.success(t("toast.accountDetailsCopied"));
      }
    } catch (error) {
      if ((error as Error).name !== "AbortError") {
        navigator.clipboard.writeText(shareData.text);
        toast.success(t("toast.accountDetailsCopied"));
      }
    }
  };

  return (
    <MobileLayout showBackButton onBack={() => navigate(-1)}>
      <div className="flex flex-col min-h-[calc(100vh-56px)] pb-28">
        {/* Title */}
        <div className="pt-4 pb-4 px-6">
          <h1 className="text-2xl font-bold text-center text-foreground">
            {t("topUp.viaBankTransfer")}
          </h1>
        </div>

        {/* Subtitle */}
        <div className="text-center pb-4">
          <span className="text-sm text-muted-foreground tracking-wide">
            {t("topUp.uaeDomesticOnly")}
          </span>
        </div>

        {/* Bank Details Card */}
        <div className="px-6 flex-1">
          <div className="bg-muted rounded-2xl p-5 space-y-4">
            {bankDetails.map((detail, index) => (
              <div
                key={index}
                className="flex items-start justify-between gap-3"
              >
                <div className="flex-1">
                  <p className="text-sm text-muted-foreground">{detail.label}</p>
                  <p className="font-semibold text-foreground break-all">
                    {detail.value}
                  </p>
                </div>
                <button
                  onClick={() => handleCopy(detail.value, detail.label)}
                  className="p-2 hover:bg-background/50 rounded-lg transition-colors flex-shrink-0"
                >
                  <Copy className="w-5 h-5 text-muted-foreground" />
                </button>
              </div>
            ))}
          </div>

          {/* Fee Details Card */}
          <div className="bg-muted rounded-2xl p-5 mt-4 space-y-3">
            {feeDetails.map((detail, index) => (
              <div key={index} className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">
                  {detail.label}
                </span>
                <span className="font-semibold text-foreground">
                  {detail.value}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Fixed Share Button */}
      <div className="fixed bottom-0 left-0 right-0 p-6 max-w-[800px] mx-auto">
        <button
          onClick={handleShare}
          className="w-full bg-primary/90 text-white font-semibold py-4 rounded-xl hover:bg-primary transition-all flex items-center justify-center gap-2 active:scale-95 backdrop-blur-2xl border-2 border-white/50 shadow-lg"
        >
          <Share2 className="w-5 h-5" />
          {t("topUp.shareAedDetails")}
        </button>
      </div>
    </MobileLayout>
  );
};

export default TopUpBankDetails;
