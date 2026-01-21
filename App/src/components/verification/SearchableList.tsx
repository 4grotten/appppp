import { Search, X, ChevronLeft } from "lucide-react";
import { useState, useMemo, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useTranslation } from "react-i18next";

interface SearchableListItem {
  id: string;
  label: string;
}

interface SearchableListProps {
  title: string;
  items: SearchableListItem[];
  value: string | null;
  onChange: (value: string) => void;
  onClose: () => void;
  searchPlaceholder?: string;
}

export const SearchableList = ({
  title,
  items,
  value,
  onChange,
  onClose,
  searchPlaceholder = "Search",
}: SearchableListProps) => {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isSearchOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isSearchOpen]);

  const filteredItems = useMemo(() => {
    if (!search) return items;
    return items.filter((item) =>
      item.label.toLowerCase().includes(search.toLowerCase())
    );
  }, [items, search]);

  const handleCloseSearch = () => {
    setIsSearchOpen(false);
    setSearch("");
  };

  return (
    <div className="fixed inset-0 z-50 bg-background animate-slide-up">
      {/* Header */}
      <div className="sticky top-0 z-50 bg-background/95 backdrop-blur-sm border-b border-border">
        {/* Normal header with title */}
        {!isSearchOpen && (
          <div className="flex items-center justify-between h-14 px-4">
            <button
              onClick={onClose}
              className="flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
              <span className="text-sm">{t('common.back')}</span>
            </button>
            
            <h2 className="text-[17px] font-semibold absolute left-1/2 -translate-x-1/2">
              {title}
            </h2>
            
            <button
              onClick={() => setIsSearchOpen(true)}
              className="w-8 h-8 rounded-full bg-secondary/80 flex items-center justify-center"
            >
              <Search className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Search header - iOS style */}
        {isSearchOpen && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center gap-3 px-4 py-2"
          >
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-[18px] h-[18px] text-muted-foreground/60" />
              <input
                ref={inputRef}
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={searchPlaceholder}
                className="w-full pl-10 pr-8 py-[9px] rounded-[10px] bg-secondary focus:outline-none text-[17px] placeholder:text-muted-foreground/60"
              />
              {search && (
                <button
                  onClick={() => setSearch("")}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 w-[18px] h-[18px] rounded-full bg-muted-foreground/40 flex items-center justify-center"
                >
                  <X className="w-3 h-3 text-background" strokeWidth={3} />
                </button>
              )}
            </div>
            
            <button
              onClick={handleCloseSearch}
              className="text-primary text-[17px] flex-shrink-0"
            >
              {t('common.cancel')}
            </button>
          </motion.div>
        )}
      </div>

      {/* List */}
      <div className="overflow-y-auto h-[calc(100vh-60px)]">
        {filteredItems.map((item) => (
          <button
            key={item.id}
            onClick={() => {
              onChange(item.id);
              onClose();
            }}
            className={`w-full flex items-center justify-between px-4 py-4 border-b border-border hover:bg-secondary/50 transition-colors ${
              value === item.id ? "bg-primary/5" : ""
            }`}
          >
            <span>{item.label}</span>
            {value === item.id && (
              <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center">
                <span className="text-primary-foreground text-sm">✓</span>
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
};
