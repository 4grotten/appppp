import { motion } from "framer-motion";

const SplashScreen = () => {
  return (
    <motion.div 
      initial={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5, ease: "easeInOut" }}
      className="fixed inset-0 bg-gradient-to-br from-background via-background to-muted flex items-center justify-center z-50"
    >
      <div className="flex flex-col items-center gap-6">
        {/* Animated Card */}
        <motion.div
          initial={{ scale: 0.8, opacity: 0, rotateY: -30 }}
          animate={{ scale: 1, opacity: 1, rotateY: 0 }}
          transition={{ 
            duration: 0.8, 
            ease: [0.16, 1, 0.3, 1]
          }}
          className="relative"
        >
          {/* Card Shadow */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 0.3, scale: 1 }}
            transition={{ delay: 0.2, duration: 0.6 }}
            className="absolute inset-0 bg-primary/20 blur-2xl rounded-3xl transform translate-y-4"
          />
          
          {/* Main Card */}
          <div className="relative w-64 h-40 rounded-2xl bg-gradient-to-br from-primary via-primary/90 to-primary/70 p-5 shadow-2xl overflow-hidden">
            {/* Card Pattern */}
            <div className="absolute inset-0 opacity-10">
              <div className="absolute top-4 right-4 w-16 h-16 border-2 border-white rounded-full" />
              <div className="absolute top-6 right-6 w-12 h-12 border-2 border-white rounded-full" />
              <div className="absolute -bottom-4 -left-4 w-24 h-24 border border-white rounded-full" />
            </div>
            
            {/* Shine Effect */}
            <motion.div
              initial={{ x: "-100%" }}
              animate={{ x: "200%" }}
              transition={{ 
                duration: 1.5, 
                delay: 0.5,
                repeat: Infinity,
                repeatDelay: 2
              }}
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent skew-x-12"
            />
            
            {/* Card Content */}
            <div className="relative h-full flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: "3rem" }}
                  transition={{ delay: 0.4, duration: 0.3 }}
                  className="h-1 bg-white/40 rounded-full"
                />
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.5, duration: 0.4 }}
                  className="text-white font-bold text-xl italic tracking-tight"
                  style={{ fontFamily: 'Arial, sans-serif' }}
                >
                  VISA
                </motion.div>
              </div>
              
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6, duration: 0.4 }}
                className="text-white font-medium text-sm tracking-widest"
              >
                •••• •••• •••• ••••
              </motion.div>
              
              <div className="flex items-end justify-end">
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.7, duration: 0.4 }}
                  className="text-white font-bold text-sm tracking-wide"
                >
                  Easy Card
                </motion.div>
              </div>
            </div>
          </div>
        </motion.div>
        
        {/* Easy Card Text */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8, duration: 0.5 }}
          className="text-center"
        >
          <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
            Easy Card
          </h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1, duration: 0.4 }}
            className="text-muted-foreground text-sm mt-1"
          >
            Your digital wallet
          </motion.p>
        </motion.div>
        
        {/* Loading Dots */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2 }}
          className="flex gap-1.5"
        >
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              animate={{ 
                scale: [1, 1.3, 1],
                opacity: [0.5, 1, 0.5]
              }}
              transition={{ 
                duration: 0.8, 
                repeat: Infinity,
                delay: i * 0.15
              }}
              className="w-2 h-2 rounded-full bg-primary"
            />
          ))}
        </motion.div>
      </div>
    </motion.div>
  );
};

export default SplashScreen;
