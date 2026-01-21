import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Check, ChevronDown, X } from "lucide-react";
import { toast } from "sonner";
import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
} from "@/components/ui/drawer";

const getLanguages = (t: (key: string) => string) => [
  { code: "system", name: t("settings.languages.system"), flag: "🌐" },
  { code: "ru", name: t("settings.languages.russian"), flag: "🇷🇺" },
  { code: "en", name: t("settings.languages.english"), flag: "🇺🇸" },
  { code: "de", name: t("settings.languages.german"), flag: "🇩🇪" },
  { code: "tr", name: t("settings.languages.turkish"), flag: "🇹🇷" },
  { code: "zh", name: t("settings.languages.chinese"), flag: "🇨🇳" },
  { code: "ar", name: t("settings.languages.arabic"), flag: "🇦🇪" },
  { code: "es", name: t("settings.languages.spanish"), flag: "🇪🇸" },
];

export const LanguageSwitcher = () => {
  const { i18n, t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState(
    localStorage.getItem("language") || "system"
  );

  const languages = getLanguages(t);
  const currentLang = languages.find((l) => l.code === selectedLanguage) || 
    languages.find((l) => l.code === i18n.language) || 
    languages[2]; // Default to English

  const handleLanguageSelect = (code: string) => {
    setSelectedLanguage(code);
    const selectedLang = languages.find((l) => l.code === code);
    
    if (code === "system") {
      const browserLang = navigator.language.split("-")[0];
      const supportedLangs = ["en", "ru", "de", "tr", "zh", "ar", "es"];
      const detectedLang = supportedLangs.includes(browserLang) ? browserLang : "en";
      i18n.changeLanguage(detectedLang);
      const detectedLangName = languages.find((l) => l.code === detectedLang)?.name || "English";
      toast.success(t("toast.languageSystem", { language: detectedLangName }));
    } else {
      i18n.changeLanguage(code);
      toast.success(t("toast.languageChanged", { language: selectedLang?.name }));
    }
    
    localStorage.setItem("language", code);
    setOpen(false);
  };

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-full bg-secondary hover:bg-muted transition-colors"
      >
        <span className="text-base">{currentLang.flag}</span>
        <span className="text-sm font-medium text-foreground uppercase">
          {currentLang.code === "system" ? i18n.language : currentLang.code}
        </span>
        <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />
      </button>

      <Drawer open={open} onOpenChange={setOpen}>
        <DrawerContent className="bg-background">
          <DrawerHeader className="relative border-b border-border">
            <DrawerTitle className="text-center text-lg font-semibold">
              {t("settings.applicationLanguage")}
            </DrawerTitle>
            <button
              onClick={() => setOpen(false)}
              className="absolute right-4 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-muted flex items-center justify-center"
            >
              <X className="w-4 h-4 text-muted-foreground" />
            </button>
          </DrawerHeader>
          <div className="py-4">
            {languages.map((language) => (
              <button
                key={language.code}
                onClick={() => handleLanguageSelect(language.code)}
                className="w-full flex items-center justify-between px-6 py-4 hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <span className="text-2xl">{language.flag}</span>
                  <span className="text-foreground font-medium">{language.name}</span>
                </div>
                {selectedLanguage === language.code && (
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