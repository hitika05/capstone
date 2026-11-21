import { motion } from "framer-motion";
import { Mic, Sparkles, ArrowRight } from "lucide-react";
import heroBg from "@/assets/hero-bg.jpg";
import stickerChai from "@/assets/sticker-chai.png";
import stickerFlower from "@/assets/sticker-flower.png";
import stickerTailor from "@/assets/sticker-tailor.png";
import stickerSweets from "@/assets/sticker-sweets.png";

const floatingStickers = [
  { src: stickerChai, alt: "Chai stall", position: "top-[12%] left-[4%]", size: "w-28 md:w-36", delay: 0.8, floatDuration: 3 },
  { src: stickerFlower, alt: "Flower shop", position: "top-[18%] right-[4%]", size: "w-24 md:w-32", delay: 1.1, floatDuration: 3.5 },
  { src: stickerTailor, alt: "Tailor shop", position: "bottom-[18%] left-[6%]", size: "w-24 md:w-32", delay: 1.4, floatDuration: 4 },
  { src: stickerSweets, alt: "Sweet shop", position: "bottom-[14%] right-[5%]", size: "w-28 md:w-36", delay: 1.0, floatDuration: 3.2 },
];

const HeroSection = () => {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      <div className="absolute inset-0">
        <img src={heroBg} alt="" className="w-full h-full object-cover" />
        <div className="absolute inset-0 bg-secondary/80" />
      </div>

      {/* Floating business stickers */}
      {floatingStickers.map((sticker, i) => (
        <motion.div
          key={i}
          className={`absolute z-10 pointer-events-none hidden md:block ${sticker.position} ${sticker.size}`}
          initial={{ opacity: 0, scale: 0.4, rotate: -12 }}
          animate={{
            opacity: [0, 0.92, 0.92],
            scale: [0.4, 1.05, 1],
            rotate: [-12, 3, 0],
            y: [0, 0, -8, 0],
          }}
          transition={{
            opacity: { delay: sticker.delay, duration: 0.6 },
            scale: { delay: sticker.delay, duration: 0.7, type: "spring", bounce: 0.45 },
            rotate: { delay: sticker.delay, duration: 0.7 },
            y: { delay: sticker.delay + 0.8, duration: sticker.floatDuration, repeat: Infinity, ease: "easeInOut" },
          }}
        >
          <img
            src={sticker.src}
            alt={sticker.alt}
            className="w-full drop-shadow-xl"
          />
        </motion.div>
      ))}

      <div className="relative z-20 container mx-auto px-6 py-24 text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="max-w-4xl mx-auto"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-2 mb-8"
          >
            <Sparkles className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium text-primary">
              Voice-First Design for Everyone
            </span>
          </motion.div>

          <h1 className="font-heading text-5xl md:text-7xl font-bold tracking-tight text-secondary-foreground mb-6">
            Bolo, Design Karo.{" "}
            <span className="gradient-text">Apni Bhasha Mein.</span>
          </h1>

          <p className="text-lg md:text-xl text-secondary-foreground/70 max-w-2xl mx-auto mb-10 font-body">
            Create stunning logos, flyers & social media posts by simply speaking
            in Hindi or Marathi. No English. No design skills. Just your voice.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <motion.button
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.97 }}
              className="inline-flex items-center gap-3 rounded-full bg-primary px-8 py-4 text-lg font-semibold text-primary-foreground shadow-elevated transition-colors hover:bg-primary/90"
            >
              <Mic className="h-5 w-5" />
              Start Designing with Voice
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.97 }}
              className="inline-flex items-center gap-2 rounded-full border-2 border-secondary-foreground/20 px-8 py-4 text-lg font-semibold text-secondary-foreground transition-colors hover:border-primary hover:text-primary"
            >
              See How It Works
              <ArrowRight className="h-5 w-5" />
            </motion.button>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.8 }}
          className="mt-16 flex justify-center items-end gap-1"
        >
          {[...Array(24)].map((_, i) => (
            <motion.div
              key={i}
              className="w-1.5 rounded-full bg-primary/60"
              animate={{ height: [8, Math.random() * 40 + 12, 8] }}
              transition={{
                duration: 1.2 + Math.random() * 0.6,
                repeat: Infinity,
                delay: i * 0.05,
                ease: "easeInOut",
              }}
            />
          ))}
        </motion.div>
      </div>
    </section>
  );
};

export default HeroSection;
