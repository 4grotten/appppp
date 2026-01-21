import { useRef, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { motion, AnimatePresence } from "framer-motion";
import { MobileLayout } from "@/components/layout/MobileLayout";
import { PoweredByFooter } from "@/components/layout/PoweredByFooter";
import { StepIndicator } from "@/components/verification/StepIndicator";
import { Sun, Scan, Glasses, ExternalLink, Image } from "lucide-react";

const LivenessCheck = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const galleryInputRef = useRef<HTMLInputElement>(null);
  const [showCamera, setShowCamera] = useState(false);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [faceDetected, setFaceDetected] = useState(false);

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 720 }, height: { ideal: 1280 } },
        audio: false,
      });
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        setStream(mediaStream);
        setIsCameraActive(true);
        setFaceDetected(false);
        
        // Simulate face detection after 1.5 seconds
        setTimeout(() => {
          setFaceDetected(true);
        }, 1500);
      }
    } catch (error) {
      console.error("Error accessing camera:", error);
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
      setIsCameraActive(false);
    }
  };

  const handleContinue = () => {
    setShowCamera(true);
    setTimeout(() => startCamera(), 100);
  };

  const handleCapture = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.drawImage(video, 0, 0);
        const imageData = canvas.toDataURL("image/jpeg");
        setCapturedImage(imageData);
        stopCamera();
      }
    }
  };

  const handleRetry = () => {
    setCapturedImage(null);
    startCamera();
  };

  const handleUsePhoto = () => {
    stopCamera();
    navigate("/verify/processing");
  };

  const handleGalleryClick = () => {
    galleryInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setCapturedImage(event.target?.result as string);
        stopCamera();
      };
      reader.readAsDataURL(file);
    }
  };

  const handleBack = () => {
    if (capturedImage) {
      setCapturedImage(null);
      startCamera();
    } else if (showCamera) {
      stopCamera();
      setShowCamera(false);
    } else {
      navigate("/verify/document-capture-back");
    }
  };

  // Instructions screen
  if (!showCamera) {
    return (
      <MobileLayout
        showBackButton
        onBack={() => navigate("/verify/document-capture-back")}
      >
        <div className="flex flex-col h-[calc(100vh-56px)]">
          {/* Progress */}
          <div className="px-6 py-4">
            <StepIndicator currentStep={4} totalSteps={4} />
          </div>

          <div className="flex-1 overflow-y-auto px-6 py-4 pb-28 flex flex-col items-center justify-center">
            <h1 className="text-2xl font-bold mb-8 text-center">
              {t('verify.liveness.title')}
            </h1>

            {/* Face Icon */}
            <div className="w-40 h-48 border-2 border-border rounded-3xl flex items-center justify-center mb-8 relative">
              <div className="w-20 h-24 border-2 border-foreground rounded-2xl relative">
                {/* Face outline */}
                <div className="absolute top-6 left-1/2 -translate-x-1/2 w-12 h-12 border-2 border-foreground rounded-full" />
                {/* Hand pointing */}
                <div className="absolute -right-8 top-1/2 -translate-y-1/2">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M18 8V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8" />
                    <path d="m22 12-4-4v3H12v2h6v3l4-4z" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Tips */}
            <div className="w-full space-y-3 mb-8">
              <h3 className="font-semibold">{t('verify.liveness.tips')}</h3>
              <div className="flex items-center gap-3 text-sm">
                <div className="w-6 h-6 rounded-full bg-success/20 flex items-center justify-center">
                  <Sun className="w-4 h-4 text-success" />
                </div>
                <span>{t('verify.liveness.tip1')}</span>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <div className="w-6 h-6 rounded-full bg-success/20 flex items-center justify-center">
                  <Scan className="w-4 h-4 text-success" />
                </div>
                <span>{t('verify.liveness.tip2')}</span>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <div className="w-6 h-6 rounded-full bg-destructive/20 flex items-center justify-center">
                  <Glasses className="w-4 h-4 text-destructive" />
                </div>
                <span>{t('verify.liveness.tip3')}</span>
              </div>
            </div>

            <button className="flex items-center gap-2 text-primary text-sm">
              <ExternalLink className="w-4 h-4" />
              <span>{t('verify.liveness.viewGuidelines')}</span>
            </button>

            <PoweredByFooter />
          </div>

          {/* Button */}
          <div className="karta-footer-actions">
            <button
              onClick={handleContinue}
              className="karta-btn-primary"
            >
              {t('verify.liveness.continue')}
            </button>
          </div>
        </div>
      </MobileLayout>
    );
  }

  // Camera/Preview screen
  return (
    <MobileLayout
      showBackButton
      onBack={handleBack}
    >
      <div className="flex flex-col h-[calc(100vh-56px)]">
        {/* Progress */}
        <div className="px-6 py-4">
          <StepIndicator currentStep={4} totalSteps={4} />
        </div>

        {/* Camera View Area */}
        <div className="flex-1 mx-4 mb-4 bg-[#1a2332] rounded-3xl flex flex-col items-center justify-between py-8 px-6 overflow-hidden">
          {capturedImage ? (
            /* Photo Preview Mode */
            <>
              <div className="flex-1 flex items-center justify-center w-full relative">
                <div className="relative w-[200px] h-[260px] rounded-[100px] overflow-hidden">
                  <img 
                    src={capturedImage} 
                    alt="Captured face" 
                    className="absolute inset-0 w-full h-full object-cover"
                  />
                  {/* Oval border */}
                  <div className="absolute inset-0 border-4 border-white rounded-[100px]" />
                </div>
              </div>

              {/* Label */}
              <p className="text-white text-xl font-semibold mb-6">{t('verify.liveness.yourSelfie')}</p>

              {/* Preview Controls */}
              <div className="flex items-center justify-center gap-4 w-full">
                <button
                  onClick={handleRetry}
                  className="flex-1 max-w-[140px] py-3 rounded-full bg-white/10 text-white font-medium backdrop-blur-sm"
                >
                  {t('verify.liveness.retry')}
                </button>
                <button
                  onClick={handleUsePhoto}
                  className="flex-1 max-w-[140px] py-3 rounded-full bg-white text-[#1a2332] font-medium"
                >
                  {t('verify.liveness.usePhoto')}
                </button>
              </div>
            </>
          ) : (
            /* Camera Capture Mode */
            <>
              <div className="flex-1 flex items-center justify-center w-full relative">
                {/* Video element */}
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="absolute inset-0 w-full h-full object-cover rounded-2xl scale-x-[-1]"
                />
                
                {/* Face frame overlay */}
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  {/* Dark overlay with oval cutout using CSS mask */}
                  <div 
                    className="absolute inset-0 bg-black/50"
                    style={{
                      maskImage: 'radial-gradient(ellipse 100px 130px at center, transparent 100%, black 100%)',
                      WebkitMaskImage: 'radial-gradient(ellipse 100px 130px at center, transparent 100%, black 100%)',
                    }}
                  />
                  
                  {/* Animated oval border */}
                  <div className="w-[200px] h-[260px] relative">
                    {/* Pulsing glow effect when detecting */}
                    <AnimatePresence>
                      {isCameraActive && !faceDetected && (
                        <motion.div
                          className="absolute inset-0 rounded-[100px]"
                          initial={{ opacity: 0 }}
                          animate={{ 
                            opacity: [0.3, 0.6, 0.3],
                            scale: [1, 1.02, 1],
                          }}
                          transition={{ 
                            duration: 1.5, 
                            repeat: Infinity,
                            ease: "easeInOut"
                          }}
                          style={{
                            boxShadow: '0 0 30px 10px rgba(255, 255, 255, 0.4)',
                          }}
                        />
                      )}
                    </AnimatePresence>
                    
                    {/* Success glow when face detected */}
                    <AnimatePresence>
                      {faceDetected && (
                        <motion.div
                          className="absolute inset-0 rounded-[100px]"
                          initial={{ opacity: 0 }}
                          animate={{ 
                            opacity: [0.4, 0.7, 0.4],
                            scale: [1, 1.01, 1],
                          }}
                          transition={{ 
                            duration: 2, 
                            repeat: Infinity,
                            ease: "easeInOut"
                          }}
                          style={{
                            boxShadow: '0 0 40px 15px rgba(34, 197, 94, 0.5)',
                          }}
                        />
                      )}
                    </AnimatePresence>
                    
                    {/* Main border with color transition */}
                    <motion.div 
                      className="absolute inset-0 rounded-[100px]"
                      initial={{ borderColor: 'rgba(255, 255, 255, 1)' }}
                      animate={{ 
                        borderColor: faceDetected 
                          ? 'rgba(34, 197, 94, 1)' 
                          : 'rgba(255, 255, 255, 1)',
                      }}
                      transition={{ duration: 0.5 }}
                      style={{ borderWidth: '4px', borderStyle: 'solid' }}
                    />
                    
                    {/* Corner accents */}
                    {[
                      { top: -2, left: '50%', transform: 'translateX(-50%)', width: 40, height: 4 },
                      { bottom: -2, left: '50%', transform: 'translateX(-50%)', width: 40, height: 4 },
                      { left: -2, top: '50%', transform: 'translateY(-50%)', width: 4, height: 40 },
                      { right: -2, top: '50%', transform: 'translateY(-50%)', width: 4, height: 40 },
                    ].map((style, i) => (
                      <motion.div
                        key={i}
                        className="absolute rounded-full"
                        initial={{ backgroundColor: 'rgba(255, 255, 255, 1)' }}
                        animate={{ 
                          backgroundColor: faceDetected 
                            ? 'rgba(34, 197, 94, 1)' 
                            : 'rgba(255, 255, 255, 1)',
                        }}
                        transition={{ duration: 0.5 }}
                        style={style}
                      />
                    ))}
                    
                    {/* Face placeholder when camera is not active */}
                    {!isCameraActive && (
                      <div className="absolute inset-0 bg-[#5a6575]/60 rounded-[100px] flex items-center justify-center">
                        <svg width="80" height="80" viewBox="0 0 24 24" fill="none" className="text-[#9ca3af]/70">
                          <circle cx="12" cy="8" r="4" stroke="currentColor" strokeWidth="1.5"/>
                          <path d="M20 21c0-4.418-3.582-8-8-8s-8 3.582-8 8" stroke="currentColor" strokeWidth="1.5"/>
                        </svg>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Label */}
              <motion.p 
                className="text-xl font-semibold mb-6 relative z-10"
                animate={{ 
                  color: faceDetected ? 'rgb(34, 197, 94)' : 'rgb(255, 255, 255)' 
                }}
                transition={{ duration: 0.5 }}
              >
                {faceDetected ? t('verify.liveness.faceDetected') : t('verify.liveness.positionFace')}
              </motion.p>

              {/* Controls */}
              <div className="flex items-center justify-center gap-12 w-full relative z-10">
                {/* Gallery button */}
                <button
                  onClick={handleGalleryClick}
                  className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center backdrop-blur-sm"
                >
                  <Image className="w-6 h-6 text-white" />
                </button>

                {/* Camera shutter button */}
                <button
                  onClick={handleCapture}
                  className="w-16 h-16 rounded-full border-4 border-white flex items-center justify-center"
                >
                  <div className="w-12 h-12 rounded-full bg-white" />
                </button>

                {/* Spacer for symmetry */}
                <div className="w-12 h-12" />
              </div>
            </>
          )}
        </div>

        {/* Hidden elements */}
        <canvas ref={canvasRef} className="hidden" />
        <input
          ref={galleryInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={handleFileChange}
        />
      </div>
    </MobileLayout>
  );
};

export default LivenessCheck;
