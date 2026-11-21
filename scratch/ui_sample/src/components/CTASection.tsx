import { motion } from "framer-motion";
import { Mic } from "lucide-react";

const CTASection = () => {
  return (
    <section className="py-24 px-6">
      <div className="container mx-auto max-w-3xl text-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="rounded-3xl bg-secondary p-12 md:p-16 shadow-elevated"
        >
          <h2 className="font-heading text-3xl md:text-5xl font-bold text-secondary-foreground mb-4">
            Apna design banao,{" "}
            <span className="gradient-text">apni awaaz se.</span>
          </h2>
          <p className="text-secondary-foreground/70 text-lg mb-10 max-w-lg mx-auto">
            Join thousands of micro-entrepreneurs creating professional designs
            in their own language.
          </p>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.97 }}
            className="inline-flex items-center gap-3 rounded-full bg-primary px-10 py-5 text-lg font-bold text-primary-foreground shadow-elevated transition-colors hover:bg-primary/90"
          >
            <Mic className="h-6 w-6" />
            Shuru Karo — It's Free
          </motion.button>
        </motion.div>
      </div>
    </section>
  );
};

export default CTASection;
