import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { MobileLayout } from "@/components/layout/MobileLayout";
import { PoweredByFooter } from "@/components/layout/PoweredByFooter";
import { Check, FileText } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";

interface TermItem {
  id: string;
  labelKey: string;
  link?: string;
  checked: boolean;
}

const AcceptTerms = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [cardTermsOpen, setCardTermsOpen] = useState(false);
  const [terms, setTerms] = useState<TermItem[]>([
    { id: "esign", labelKey: "verify.terms.esign", link: "#", checked: true },
    { id: "card-terms", labelKey: "verify.terms.cardTerms", link: "#", checked: true },
    { id: "privacy", labelKey: "verify.terms.privacyPolicy", link: "#", checked: true },
    { id: "certify", labelKey: "verify.terms.certify", checked: true },
    { id: "acknowledge", labelKey: "verify.terms.acknowledge", checked: true },
  ]);

  const allChecked = terms.every((t) => t.checked);

  const toggleTerm = (id: string) => {
    setTerms(terms.map((t) => (t.id === id ? { ...t, checked: !t.checked } : t)));
  };

  const checkAll = () => {
    const shouldCheck = !allChecked;
    setTerms(terms.map((t) => ({ ...t, checked: shouldCheck })));
  };

  const handleTermClick = (term: TermItem, e: React.MouseEvent) => {
    if (term.id === "card-terms") {
      e.stopPropagation();
      setCardTermsOpen(true);
    }
  };

  return (
    <MobileLayout
      showBackButton
      onBack={() => navigate("/verify")}
      rightAction={<span className="text-sm text-muted-foreground">•••</span>}
    >
      <div className="flex flex-col h-[calc(100vh-56px)]">
        <div className="flex-1 overflow-y-auto px-6 py-8 pb-28">
          {/* Header */}
          <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
            <FileText className="w-8 h-8 text-primary" />
          </div>
          <h1 className="text-2xl font-bold mb-2">{t('verify.terms.title')}</h1>
          <p className="text-muted-foreground whitespace-pre-line">
            {t('verify.terms.description')}
          </p>
        </div>

        {/* Terms List */}
        <div className="flex-1 space-y-4">
          {terms.map((term) => (
            <button
              key={term.id}
              onClick={() => toggleTerm(term.id)}
              className="w-full flex items-start gap-3 text-left"
            >
              <div
                className={`w-6 h-6 rounded-lg flex-shrink-0 flex items-center justify-center mt-0.5 transition-all ${
                  term.checked
                    ? "bg-primary text-white"
                    : "border-2 border-border"
                }`}
              >
                {term.checked && <Check className="w-4 h-4" strokeWidth={3} />}
              </div>
              <span className="text-sm">
                {term.link ? (
                  <>
                    {t('verify.terms.iAccept')}{" "}
                    <span 
                      className="text-primary underline"
                      onClick={(e) => handleTermClick(term, e)}
                    >
                      {t(term.labelKey)}
                    </span>
                  </>
                ) : (
                  t(term.labelKey)
                )}
              </span>
            </button>
            ))}
          </div>

          <PoweredByFooter />
        </div>

        {/* Footer */}
        <div className="karta-footer-actions">
          <button
            onClick={() => navigate("/verify/steps")}
            disabled={!allChecked}
            className={`karta-btn-primary ${
              !allChecked ? "opacity-50 cursor-not-allowed" : ""
            }`}
          >
            {t('verify.terms.button')}
          </button>
        </div>
      </div>

      {/* Card Terms Modal */}
      <Dialog open={cardTermsOpen} onOpenChange={setCardTermsOpen}>
        <DialogContent className="w-full h-full max-w-none max-h-none p-0 rounded-none">
          <DialogHeader className="p-6 pb-0">
            <DialogTitle className="text-xl">{t('verify.terms.cardTerms')}</DialogTitle>
            <p className="text-xs text-muted-foreground">Last updated: February 17, 2025</p>
          </DialogHeader>
          <ScrollArea className="h-[calc(100vh-120px)] px-6 pb-6">
            <div className="space-y-4 text-sm text-muted-foreground pr-4">
              <p>
                You are applying for an Easy Card Personal card. Your agreement to this Consent allows us to provide you with legally required disclosures, agreements, statements, and other documents (collectively, the "Documents") in electronic form and to authorize and sign these Documents electronically using our platform (the "Service"). If you do not consent to electronic communications and electronic signatures, you will not be able to use the Service.
              </p>

              <div>
                <h3 className="font-semibold text-foreground mb-2">Duration of Consent</h3>
                <p>
                  Your consent remains in effect until either you or we terminate your use of the Service or your Easy Card Personal card, or until you revoke your consent to receive electronic communications.
                </p>
              </div>

              <div>
                <h3 className="font-semibold text-foreground mb-2">Methods of Providing Documents</h3>
                <p>
                  We may provide Documents electronically through downloadable files, including PDF format, accessible via our website or email communications. You are responsible for reviewing these Documents in a timely manner.
                </p>
              </div>

              <div>
                <h3 className="font-semibold text-foreground mb-2">Access to Paper Copies</h3>
                <p>
                  You can save or print copies of the Documents using your browser's or PDF viewer's "print" or "save" function. We retain copies of Documents for legally required periods and can provide them upon request. We encourage you to save or print copies for future reference.
                </p>
                <p className="mt-2">
                  You may request a paper copy of any Document at no additional cost by contacting us at support@easycard.io.
                </p>
              </div>

              <div>
                <h3 className="font-semibold text-foreground mb-2">Our Right to Send Paper Copies</h3>
                <p>
                  We reserve the right to provide you with paper copies of Documents at our discretion, even if you have opted for electronic delivery. This may occur in cases of system failure or suspected fraud.
                </p>
              </div>

              <div>
                <h3 className="font-semibold text-foreground mb-2">Technical Requirements</h3>
                <p>To access and retain Documents, you need a device with:</p>
                <ul className="list-disc list-inside mt-2 space-y-1">
                  <li>Internet access;</li>
                  <li>A web browser supporting 128-bit encryption (we support the latest versions of Chrome®, Firefox®, Microsoft Edge®, or Safari®);</li>
                  <li>A program capable of viewing, saving, and printing PDF files (such as Adobe® Reader® 4.0 or higher).</li>
                </ul>
              </div>

              <div>
                <h3 className="font-semibold text-foreground mb-2">Withdrawing Consent</h3>
                <p>
                  You may revoke your consent at any time without incurring any fees. However, doing so may affect your ability to receive our services online. To withdraw your consent, contact us at support@easycard.io. Note that revoking consent does not affect the validity of Documents already provided electronically.
                </p>
              </div>

              <div>
                <h3 className="font-semibold text-foreground mb-2">Acknowledging Ability to Access and Consenting to Electronic Communications</h3>
                <p>By confirming that you have read and agreed to these terms, you are confirming that:</p>
                <ol className="list-decimal list-inside mt-2 space-y-1">
                  <li>you have access to a computer system that meets the requirements set forth above;</li>
                  <li>you agree to receive the Documents electronically; and</li>
                  <li>you are able to access and print or store information presented to you.</li>
                </ol>
              </div>
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>
    </MobileLayout>
  );
};

export default AcceptTerms;
