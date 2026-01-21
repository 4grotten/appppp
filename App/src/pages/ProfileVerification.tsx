import { useNavigate } from "react-router-dom";
import { MobileLayout } from "@/components/layout/MobileLayout";
import { Fingerprint, ShieldCheck, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

const ProfileVerification = () => {
  const navigate = useNavigate();

  return (
    <MobileLayout
      showBackButton
      onBack={() => navigate(-1)}
    >
      <div className="flex flex-col items-center justify-center px-6 pt-16 pb-8">
        {/* Icon */}
        <div className="w-24 h-24 rounded-full bg-primary/10 flex items-center justify-center mb-6">
          <Fingerprint className="w-12 h-12 text-primary" />
        </div>

        {/* Title */}
        <h1 className="text-2xl font-bold text-foreground mb-3 text-center">
          Verify Your Identity
        </h1>

        {/* Description */}
        <p className="text-muted-foreground text-center mb-8 max-w-sm">
          Complete the verification process to unlock all features and increase your account limits.
        </p>

        {/* Benefits */}
        <div className="w-full bg-card rounded-2xl p-5 mb-8 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-primary" />
            </div>
            <div>
              <p className="font-medium text-foreground">Secure & Private</p>
              <p className="text-sm text-muted-foreground">Your data is encrypted and protected</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <ArrowRight className="w-5 h-5 text-primary" />
            </div>
            <div>
              <p className="font-medium text-foreground">Quick Process</p>
              <p className="text-sm text-muted-foreground">Takes only 2-3 minutes to complete</p>
            </div>
          </div>
        </div>

        {/* CTA Button */}
        <Button
          onClick={() => navigate("/verify")}
          className="w-full h-14 text-base font-semibold rounded-2xl bg-primary/90 backdrop-blur-2xl border-2 border-white/50 text-primary-foreground gap-2 shadow-lg hover:bg-primary"
        >
          Start Verification
          <ArrowRight className="w-5 h-5" />
        </Button>
      </div>
    </MobileLayout>
  );
};

export default ProfileVerification;
