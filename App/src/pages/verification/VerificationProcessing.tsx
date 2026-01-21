import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { MobileLayout } from "@/components/layout/MobileLayout";
import { PoweredByFooter } from "@/components/layout/PoweredByFooter";

const VerificationProcessing = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setTimeout(() => navigate("/verify/complete"), 500);
          return 100;
        }
        return prev + 10;
      });
    }, 300);

    return () => clearInterval(interval);
  }, [navigate]);

  return (
    <MobileLayout>
      <div className="flex flex-col min-h-[calc(100vh-56px)] items-center justify-center px-6">
        {/* Animated Face */}
        <div className="relative w-40 h-40 mb-8">
          {/* Outer ring */}
          <div className="absolute inset-0 rounded-full border-4 border-border">
            <div
              className="absolute inset-0 rounded-full border-4 border-foreground border-t-transparent animate-spin"
              style={{ animationDuration: "2s" }}
            />
          </div>

          {/* Face */}
          <div className="absolute inset-4 rounded-full bg-background border-2 border-foreground flex items-center justify-center">
            <div className="w-20 h-20 relative">
              {/* Eyes */}
              <div className="absolute top-4 left-3 w-4 h-6 bg-foreground rounded-full" />
              <div className="absolute top-4 right-3 w-4 h-6 bg-foreground rounded-full" />
              {/* Smile */}
              <div className="absolute bottom-2 left-1/2 -translate-x-1/2 w-10 h-5 border-b-4 border-foreground rounded-b-full" />
            </div>
          </div>
        </div>

        <p className="text-xl font-medium mb-4">{t('verify.processing.connecting')}</p>

        {/* Progress bar */}
        <div className="w-full max-w-xs h-1 bg-border rounded-full overflow-hidden">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>

        <p className="text-sm text-muted-foreground mt-4">
          {t('verify.processing.verifying')}
        </p>
        <p className="text-sm text-muted-foreground">
          {t('verify.processing.pleaseWait')}
        </p>

        <div className="mt-8">
          <PoweredByFooter />
        </div>
      </div>
    </MobileLayout>
  );
};

export default VerificationProcessing;
