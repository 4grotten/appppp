import { Check } from "lucide-react";

interface VerificationStep {
  id: string;
  title: string;
  description?: string;
  icon: React.ReactNode;
  status: "pending" | "current" | "completed";
}

interface VerificationStepsListProps {
  steps: VerificationStep[];
}

export const VerificationStepsList = ({ steps }: VerificationStepsListProps) => {
  return (
    <div className="space-y-4">
      {steps.map((step, index) => (
        <div key={step.id} className="flex items-start gap-4">
          <div
            className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
              step.status === "completed"
                ? "bg-primary text-primary-foreground"
                : step.status === "current"
                ? "bg-secondary text-foreground border-2 border-foreground"
                : "bg-secondary text-muted-foreground"
            }`}
          >
            {step.status === "completed" ? (
              <Check className="w-5 h-5" />
            ) : (
              step.icon
            )}
          </div>
          <div className="flex-1 pt-2">
            <p className="text-xs text-muted-foreground">Step {index + 1}</p>
            <p className="font-medium">{step.title}</p>
            {step.description && (
              <p className="text-sm text-muted-foreground">{step.description}</p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};
