import { Check, Circle } from "lucide-react";

interface RadioOption {
  id: string;
  label: string;
  description?: string;
}

interface RadioGroupProps {
  options: RadioOption[];
  value: string | null;
  onChange: (value: string) => void;
  className?: string;
}

export const RadioGroup = ({
  options,
  value,
  onChange,
  className = "",
}: RadioGroupProps) => {
  return (
    <div className={`space-y-2 ${className}`}>
      {options.map((option) => (
        <button
          key={option.id}
          onClick={() => onChange(option.id)}
          className={`w-full flex items-center justify-between p-4 rounded-xl border transition-all ${
            value === option.id
              ? "border-primary bg-primary/5"
              : "border-border hover:border-muted-foreground"
          }`}
        >
          <div className="text-left">
            <p className="font-medium">{option.label}</p>
            {option.description && (
              <p className="text-sm text-muted-foreground">{option.description}</p>
            )}
          </div>
          <div
            className={`w-6 h-6 rounded-full flex items-center justify-center ${
              value === option.id
                ? "bg-primary text-primary-foreground"
                : "border-2 border-border"
            }`}
          >
            {value === option.id && <Check className="w-4 h-4" />}
          </div>
        </button>
      ))}
    </div>
  );
};
