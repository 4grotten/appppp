import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronLeft, MoreHorizontal, Heart, ArrowUp } from "lucide-react";
import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { motion, AnimatePresence } from "framer-motion";

interface Message {
  id: string;
  text: string;
  sender: "user" | "ai";
  timestamp: Date;
  replyTo?: {
    name: string;
    text: string;
  };
}

const Chat = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  
  const initialMessages: Message[] = [
    {
      id: "1",
      text: t("chat.welcomeMessage"),
      sender: "ai",
      timestamp: new Date(2025, 8, 23, 2, 49),
    },
  ];
  
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [inputValue, setInputValue] = useState("");
  const [likedMessages, setLikedMessages] = useState<Set<string>>(new Set());
  const [animatingLikes, setAnimatingLikes] = useState<Set<string>>(new Set());
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (!inputValue.trim()) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      text: inputValue.trim(),
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, newMessage]);
    setInputValue("");

    // Simulate AI response with reply
    setTimeout(() => {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        text: t("chat.thankYouMessage"),
        sender: "ai",
        timestamp: new Date(),
        replyTo: {
          name: "Rinat Kamiev",
          text: newMessage.text,
        },
      };
      setMessages((prev) => [...prev, aiResponse]);
    }, 1000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleLike = (messageId: string) => {
    const isCurrentlyLiked = likedMessages.has(messageId);
    
    setLikedMessages((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });

    // Trigger burst animation only when liking (not unliking)
    if (!isCurrentlyLiked) {
      setAnimatingLikes((prev) => new Set(prev).add(messageId));
      setTimeout(() => {
        setAnimatingLikes((prev) => {
          const newSet = new Set(prev);
          newSet.delete(messageId);
          return newSet;
        });
      }, 800);
    }
  };

  const formatDateTime = (date: Date) => {
    const day = date.getDate().toString().padStart(2, "0");
    const month = (date.getMonth() + 1).toString().padStart(2, "0");
    const year = date.getFullYear();
    const hours = date.getHours().toString().padStart(2, "0");
    const minutes = date.getMinutes().toString().padStart(2, "0");
    return `${day}.${month}.${year} ${hours}:${minutes}`;
  };

  return (
    <div className="min-h-screen bg-background flex flex-col max-w-[800px] mx-auto">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-background/95 backdrop-blur-sm border-b border-border">
        <div className="flex items-center justify-center h-14 px-4">
          <h1 className="text-lg font-semibold text-foreground">Rinat Kamiev</h1>
        </div>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 pb-40">
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              "flex gap-3",
              message.sender === "user" ? "flex-row-reverse" : "flex-row"
            )}
          >
            {/* Avatar */}
            {message.sender === "ai" ? (
              <div className="flex-shrink-0">
                <div className="w-12 h-12 rounded-full bg-[#2d3748] flex items-center justify-center">
                  <span className="text-white text-[8px] font-medium">apofiz.com</span>
                </div>
              </div>
            ) : (
              <Avatar className="w-12 h-12 flex-shrink-0 ring-2 ring-[#00b4d8]">
                <AvatarImage 
                  src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200&h=200&fit=crop&crop=face" 
                  alt="User" 
                />
                <AvatarFallback>RK</AvatarFallback>
              </Avatar>
            )}

            {/* Message Bubble */}
            <div className="bg-card rounded-2xl px-4 py-3 max-w-[75%] shadow-[0_4px_20px_rgba(0,0,0,0.12)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.3)]">
              {/* Sender Name */}
              <div className="mb-1">
                <span className="text-[#00b4d8] font-semibold text-sm">
                  {message.sender === "ai" ? "Ai" : "Rinat Kamiev"}
                </span>
                <span className="text-muted-foreground text-xs ml-2">
                  {message.sender === "ai" ? t("chat.aiAssistant") : t("chat.owner")}
                </span>
              </div>

              {/* Reply Quote */}
              {message.replyTo && (
                <div className="border-l-2 border-[#00b4d8] pl-2 mb-2 py-1">
                  <span className="text-[#00b4d8] text-xs font-medium">
                    {t("chat.replyTo")} {message.replyTo.name}
                  </span>
                  <p className="text-muted-foreground text-xs">{message.replyTo.text}</p>
                </div>
              )}

              {/* Message Text */}
              <p className="text-foreground text-sm leading-relaxed">
                {message.text}
              </p>

              {/* Footer: Like & Timestamp */}
              <div className="flex items-center justify-between mt-2 pt-1">
                <button
                  onClick={() => toggleLike(message.id)}
                  className="relative transition-transform active:scale-90"
                >
                  {/* Burst animation overlay */}
                  <AnimatePresence>
                    {animatingLikes.has(message.id) && (
                      <motion.div
                        initial={{ scale: 0, opacity: 1 }}
                        animate={{ scale: 2.5, opacity: 0 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.6, ease: "easeOut" }}
                        className="absolute inset-0 flex items-center justify-center pointer-events-none"
                      >
                        <Heart className="w-5 h-5 fill-red-500 text-red-500" />
                      </motion.div>
                    )}
                  </AnimatePresence>
                  
                  {/* Main heart icon */}
                  <motion.div
                    animate={likedMessages.has(message.id) ? {
                      scale: [1, 1.3, 0.9, 1.1, 1],
                    } : { scale: 1 }}
                    transition={{ duration: 0.4, ease: "easeOut" }}
                  >
                    <Heart
                      className={cn(
                        "w-5 h-5 transition-colors duration-200",
                        likedMessages.has(message.id)
                          ? "fill-red-500 text-red-500"
                          : "text-red-400"
                      )}
                    />
                  </motion.div>
                </button>
                <span className="text-muted-foreground text-xs">
                  {formatDateTime(message.timestamp)}
                </span>
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area - Fixed at bottom */}
      <div className="fixed bottom-20 left-0 right-0 max-w-[800px] mx-auto px-4 pb-4">
        <div className="bg-card/80 backdrop-blur-xl rounded-full flex items-center px-4 py-2 shadow-lg">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={t("chat.messagePlaceholder")}
            className="flex-1 bg-transparent text-base text-foreground placeholder-muted-foreground focus:outline-none"
            style={{ fontSize: '16px' }}
          />
          <button
            onClick={handleSend}
            disabled={!inputValue.trim()}
            className={cn(
              "w-9 h-9 rounded-full flex items-center justify-center transition-all ml-2",
              inputValue.trim()
                ? "bg-[#007AFF] text-white hover:bg-[#0066DD]"
                : "bg-gray-200 text-gray-400"
            )}
          >
            <ArrowUp className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default Chat;
