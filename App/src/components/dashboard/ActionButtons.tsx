import { Plus, ArrowUp } from "lucide-react";
import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";

interface ActionButtonsProps {
  onTopUp?: () => void;
  onSend?: () => void;
}

export const ActionButtons = ({ onTopUp, onSend }: ActionButtonsProps) => {
  const { t } = useTranslation();
  
  return (
    <motion.div 
      className="flex gap-3"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1, ease: "easeOut" }}
    >
      <motion.button
        onClick={onTopUp}
        className="flex-1 flex items-center justify-center gap-2 bg-primary text-primary-foreground font-semibold py-3.5 rounded-xl hover:opacity-90 transition-all"
        whileTap={{ scale: 0.97 }}
        whileHover={{ scale: 1.02 }}
      >
        <Plus className="w-5 h-5" />
        <span>{t('dashboard.topUp')}</span>
      </motion.button>
      <motion.button
        onClick={onSend}
        className="flex-1 flex items-center justify-center gap-2 bg-primary text-primary-foreground font-semibold py-3.5 rounded-xl hover:opacity-90 transition-all"
        whileTap={{ scale: 0.97 }}
        whileHover={{ scale: 1.02 }}
      >
        <ArrowUp className="w-5 h-5" />
        <span>{t('dashboard.send')}</span>
      </motion.button>
    </motion.div>
  );
};
