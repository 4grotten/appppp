import { useRef, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { MobileLayout } from "@/components/layout/MobileLayout";
import { StepIndicator } from "@/components/verification/StepIndicator";
import { Image } from "lucide-react";

const DocumentCaptureBack = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const galleryInputRef = useRef<HTMLInputElement>(null);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);

  useEffect(() => {
    startCamera();
    return () => {
      stopCamera();
    };
  }, []);

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        setStream(mediaStream);
        setIsCameraActive(true);
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
    navigate("/verify/liveness");
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

  return (
    <MobileLayout
      showBackButton
      onBack={() => {
        stopCamera();
        navigate("/verify/document-capture-front");
      }}
    >
      <div className="flex flex-col h-[calc(100vh-56px)]">
        {/* Progress */}
        <div className="px-6 py-4">
          <StepIndicator currentStep={3} totalSteps={4} />
        </div>

        {/* Camera View Area */}
        <div className="flex-1 mx-4 mb-4 bg-[#1a2332] rounded-3xl flex flex-col items-center justify-between py-8 px-6 overflow-hidden">
          {capturedImage ? (
            /* Photo Preview Mode */
            <>
              <div className="flex-1 flex items-center justify-center w-full relative">
                <div className="w-full max-w-[320px] aspect-[1.6/1] relative rounded-xl overflow-hidden">
                  <img 
                    src={capturedImage} 
                    alt="Captured document" 
                    className="absolute inset-0 w-full h-full object-cover"
                  />
                  {/* Corner guides */}
                  <div className="absolute top-0 left-0 w-10 h-10 border-t-4 border-l-4 border-white rounded-tl-xl z-20" />
                  <div className="absolute top-0 right-0 w-10 h-10 border-t-4 border-r-4 border-white rounded-tr-xl z-20" />
                  <div className="absolute bottom-0 left-0 w-10 h-10 border-b-4 border-l-4 border-white rounded-bl-xl z-20" />
                  <div className="absolute bottom-0 right-0 w-10 h-10 border-b-4 border-r-4 border-white rounded-br-xl z-20" />
                </div>
              </div>

              {/* Label */}
              <p className="text-white text-xl font-semibold mb-6">{t('verify.capture.backSide')}</p>

              {/* Preview Controls */}
              <div className="flex items-center justify-center gap-4 w-full">
                <button
                  onClick={handleRetry}
                  className="flex-1 max-w-[140px] py-3 rounded-full bg-white/10 text-white font-medium backdrop-blur-sm"
                >
                  {t('verify.capture.retry')}
                </button>
                <button
                  onClick={handleUsePhoto}
                  className="flex-1 max-w-[140px] py-3 rounded-full bg-white text-[#1a2332] font-medium"
                >
                  {t('verify.capture.usePhoto')}
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
                  className="absolute inset-0 w-full h-full object-cover rounded-2xl"
                />
                
                {/* Document frame overlay */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="relative w-full max-w-[320px] aspect-[1.6/1]">
                    {/* Corner guides only */}
                    <div className="absolute top-0 left-0 w-10 h-10 border-t-4 border-l-4 border-white rounded-tl-xl z-20" />
                    <div className="absolute top-0 right-0 w-10 h-10 border-t-4 border-r-4 border-white rounded-tr-xl z-20" />
                    <div className="absolute bottom-0 left-0 w-10 h-10 border-b-4 border-l-4 border-white rounded-bl-xl z-20" />
                    <div className="absolute bottom-0 right-0 w-10 h-10 border-b-4 border-r-4 border-white rounded-br-xl z-20" />

                    {/* Transparent document placeholder - always visible as guide */}
                    <div className="absolute inset-0 bg-[#5a6575]/40 rounded-xl flex flex-col justify-between p-4 pointer-events-none">
                      <div className="space-y-2.5">
                        <div className="h-3.5 bg-[#9ca3af]/50 rounded-full w-full" />
                        <div className="h-3.5 bg-[#9ca3af]/50 rounded-full w-full" />
                        <div className="h-3.5 bg-[#9ca3af]/50 rounded-full w-3/4" />
                      </div>
                      <div className="flex justify-end">
                        <div className="w-1/2 h-8 bg-[#9ca3af]/40 rounded" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Label */}
              <p className="text-white text-xl font-semibold mb-6 relative z-10">{t('verify.capture.backSide')}</p>

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

export default DocumentCaptureBack;
