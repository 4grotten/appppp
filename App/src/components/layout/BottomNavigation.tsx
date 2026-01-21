import { Home, Info, MessageCircle } from "lucide-react";
import { NavLink as RouterNavLink, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useAvatar } from "@/contexts/AvatarContext";
import { motion } from "framer-motion";
import { useEffect, useRef, useState, useCallback } from "react";

const navItems = [
  { icon: Home, labelKey: "nav.home", path: "/" },
  { icon: Info, labelKey: "nav.info", path: "/info" },
  { icon: MessageCircle, labelKey: "nav.chat", path: "/chat" },
  { icon: null, labelKey: "nav.profile", path: "/settings" },
];

export const BottomNavigation = () => {
  const location = useLocation();
  const { avatarUrl } = useAvatar();
  const { t, i18n } = useTranslation();
  const hasMountedRef = useRef(false);
  const tabRefs = useRef<(HTMLAnchorElement | null)[]>([]);
  const [selectorStyle, setSelectorStyle] = useState({ left: 0, width: 0 });

  const isActive = (path: string) => {
    if (path === "/") {
      return location.pathname === "/";
    }
    return location.pathname.startsWith(path);
  };

  const activeIndex = navItems.findIndex(item => isActive(item.path));

  const updateSelector = useCallback(() => {
    const activeTab = tabRefs.current[activeIndex];
    if (activeTab) {
      const container = activeTab.parentElement;
      if (container) {
        const containerRect = container.getBoundingClientRect();
        const tabRect = activeTab.getBoundingClientRect();
        setSelectorStyle({
          left: tabRect.left - containerRect.left,
          width: tabRect.width,
        });
      }
    }
  }, [activeIndex]);

  useEffect(() => {
    hasMountedRef.current = true;
  }, []);

  useEffect(() => {
    updateSelector();
  }, [activeIndex, updateSelector, i18n.language]);

  // Update on resize
  useEffect(() => {
    window.addEventListener('resize', updateSelector);
    return () => window.removeEventListener('resize', updateSelector);
  }, [updateSelector]);

  return (
    <nav className="fixed bottom-4 left-0 right-0 z-50 px-4 max-w-[800px] mx-auto">
      <div className="bg-white/50 backdrop-blur-2xl rounded-3xl shadow-lg border border-white/30 px-2 py-1.5 max-w-[400px] mx-auto">
        <div className="flex items-center justify-around relative">
          {/* Sliding selector */}
          <motion.div
            className="absolute bg-gray-200/50 rounded-3xl"
            initial={false}
            animate={{
              left: selectorStyle.left,
              width: selectorStyle.width,
            }}
            transition={
              hasMountedRef.current
                ? { type: "spring", stiffness: 400, damping: 30 }
                : { duration: 0 }
            }
            style={{
              height: "calc(100% - 4px)",
              top: "2px",
            }}
          />
          
          {navItems.map((item, index) => {
            const active = isActive(item.path);
            
            if (item.path === "/settings") {
              return (
                <RouterNavLink
                  key={item.path}
                  to={item.path}
                  ref={(el) => { tabRefs.current[index] = el; }}
                  className="flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-3xl transition-all relative z-10"
                >
                  <Avatar className={cn(
                    "w-6 h-6 transition-all",
                    active ? "ring-2 ring-primary" : ""
                  )}>
                    <AvatarImage src={avatarUrl} alt="Profile" />
                    <AvatarFallback className="text-xs">AW</AvatarFallback>
                  </Avatar>
                  <span
                    className={cn(
                      "text-xs font-medium transition-colors",
                      active ? "text-primary" : "text-[#333333]"
                    )}
                  >
                    {t(item.labelKey)}
                  </span>
                </RouterNavLink>
              );
            }
            
            const Icon = item.icon!;
            return (
              <RouterNavLink
                key={item.path}
                to={item.path}
                ref={(el) => { tabRefs.current[index] = el; }}
                className="flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-3xl transition-all relative z-10"
              >
                <Icon
                  className={cn(
                    "w-6 h-6 transition-colors",
                    active ? "text-primary" : "text-[#333333]"
                  )}
                  strokeWidth={active ? 2.5 : 1.5}
                />
                <span
                  className={cn(
                    "text-xs font-medium transition-colors",
                    active ? "text-primary" : "text-[#333333]"
                  )}
                >
                  {t(item.labelKey)}
                </span>
              </RouterNavLink>
            );
          })}
        </div>
      </div>
    </nav>
  );
};
