import { useState, useEffect } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import SplashScreen from "./components/SplashScreen";
import Dashboard from "./pages/Dashboard";
import VirtualCard from "./pages/VirtualCard";
import MetalCard from "./pages/MetalCard";
import SendToCard from "./pages/SendToCard";
import TransactionDetails from "./pages/TransactionDetails";
import PrivacyProtection from "./pages/verification/PrivacyProtection";
import AcceptTerms from "./pages/verification/AcceptTerms";
import VerificationSteps from "./pages/verification/VerificationSteps";
import PersonalInfo from "./pages/verification/PersonalInfo";
import MonthlyVolume from "./pages/verification/MonthlyVolume";
import DocumentType from "./pages/verification/DocumentType";
import DocumentUpload from "./pages/verification/DocumentUpload";
import DocumentCaptureFront from "./pages/verification/DocumentCaptureFront";
import DocumentCaptureBack from "./pages/verification/DocumentCaptureBack";
import LivenessCheck from "./pages/verification/LivenessCheck";
import VerificationProcessing from "./pages/verification/VerificationProcessing";
import VerificationComplete from "./pages/verification/VerificationComplete";
import Settings from "./pages/Settings";
import FeesAndLimits from "./pages/FeesAndLimits";
import ProfileVerification from "./pages/ProfileVerification";
import TopUpCrypto from "./pages/TopUpCrypto";
import TopUpBank from "./pages/TopUpBank";
import TopUpBankDetails from "./pages/TopUpBankDetails";
import SendCrypto from "./pages/SendCrypto";
import SendBank from "./pages/SendBank";
import NotFound from "./pages/NotFound";
import Chat from "./pages/Chat";
import { BottomNavigation } from "./components/layout/BottomNavigation";
import { AvatarProvider } from "./contexts/AvatarContext";

const queryClient = new QueryClient();

// Routes where bottom navigation should be hidden
const hiddenNavRoutes = [
  "/verify",
  "/card/",
  "/send-to-card",
  "/top-up/",
  "/send/",
  "/transaction/",
  "/profile-verification",
];

const AppContent = () => {
  const location = useLocation();
  
  const shouldShowNav = !hiddenNavRoutes.some(route => 
    location.pathname.startsWith(route)
  );

  return (
    <>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/fees-and-limits" element={<FeesAndLimits />} />
        <Route path="/profile-verification" element={<ProfileVerification />} />
        <Route path="/profile" element={<ProfileVerification />} />
        <Route path="/info" element={<FeesAndLimits />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/card/virtual" element={<VirtualCard />} />
        <Route path="/card/metal" element={<MetalCard />} />
        <Route path="/send-to-card" element={<SendToCard />} />
        <Route path="/top-up/crypto" element={<TopUpCrypto />} />
        <Route path="/top-up/bank" element={<TopUpBank />} />
        <Route path="/top-up/bank/details" element={<TopUpBankDetails />} />
        <Route path="/send/crypto" element={<SendCrypto />} />
        <Route path="/send/bank" element={<SendBank />} />
        <Route path="/transaction/:id" element={<TransactionDetails />} />
        <Route path="/verify" element={<PrivacyProtection />} />
        <Route path="/verify/terms" element={<AcceptTerms />} />
        <Route path="/verify/steps" element={<VerificationSteps />} />
        <Route path="/verify/personal-info" element={<PersonalInfo />} />
        <Route path="/verify/monthly-volume" element={<MonthlyVolume />} />
        <Route path="/verify/document-type" element={<DocumentType />} />
        <Route path="/verify/document-upload" element={<DocumentUpload />} />
        <Route path="/verify/document-capture-front" element={<DocumentCaptureFront />} />
        <Route path="/verify/document-capture-back" element={<DocumentCaptureBack />} />
        <Route path="/verify/liveness" element={<LivenessCheck />} />
        <Route path="/verify/processing" element={<VerificationProcessing />} />
        <Route path="/verify/complete" element={<VerificationComplete />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
      <AnimatePresence>
        {shouldShowNav && (
          <motion.div
            initial={false}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 100, opacity: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
          >
            <BottomNavigation />
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

const App = () => {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 2500);

    return () => clearTimeout(timer);
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <AnimatePresence mode="wait">
          {isLoading ? (
            <SplashScreen key="splash" />
          ) : (
            <BrowserRouter>
              <AvatarProvider>
                <AppContent />
              </AvatarProvider>
            </BrowserRouter>
          )}
        </AnimatePresence>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;
