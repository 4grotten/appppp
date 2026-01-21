interface StepIndicatorProps {
  currentStep: number;
  totalSteps: number;
}

export const StepIndicator = ({ currentStep, totalSteps }: StepIndicatorProps) => {
  return (
    <div className="flex gap-2">
      {Array.from({ length: totalSteps }).map((_, index) => (
        <div
          key={index}
          className={`h-1 flex-1 rounded-full transition-all ${
            index < currentStep
              ? "bg-foreground"
              : index === currentStep
              ? "bg-foreground"
              : "bg-border"
          }`}
        />
      ))}
    </div>
  );
};
