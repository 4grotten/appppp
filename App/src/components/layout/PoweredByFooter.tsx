import apofizLogo from "@/assets/apofiz-logo.svg";

export const PoweredByFooter = () => {
  return (
    <p className="text-center text-xs text-muted-foreground mt-4 flex items-center justify-center gap-1">
      Powered by{" "}
      <img src={apofizLogo} alt="Apofiz" className="w-4 h-4 inline-block" />{" "}
      <span className="font-semibold text-foreground">Apofiz</span>
    </p>
  );
};
