import React, { createContext, useContext, useState, useEffect } from "react";

const DEFAULT_AVATAR = "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200&h=200&fit=crop&crop=face";
const AVATAR_STORAGE_KEY = "user-avatar";

interface AvatarContextType {
  avatarUrl: string;
  setAvatarUrl: (url: string) => void;
}

const AvatarContext = createContext<AvatarContextType | undefined>(undefined);

export const AvatarProvider = ({ children }: { children: React.ReactNode }) => {
  const [avatarUrl, setAvatarUrl] = useState(() => {
    const saved = localStorage.getItem(AVATAR_STORAGE_KEY);
    return saved || DEFAULT_AVATAR;
  });

  useEffect(() => {
    localStorage.setItem(AVATAR_STORAGE_KEY, avatarUrl);
  }, [avatarUrl]);

  return (
    <AvatarContext.Provider value={{ avatarUrl, setAvatarUrl }}>
      {children}
    </AvatarContext.Provider>
  );
};

export const useAvatar = () => {
  const context = useContext(AvatarContext);
  if (!context) {
    throw new Error("useAvatar must be used within an AvatarProvider");
  }
  return context;
};
