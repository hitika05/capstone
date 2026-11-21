import { motion } from "framer-motion";

const steps = [
  {
    number: "01",
    title: "Bolo",
    subtitle: "Speak your idea",
    description:
      '"Mera chai dukan ke liye ek logo banao, orange aur brown color mein"',
  },
  {
    number: "02",
    title: "Dekho",
    subtitle: "See AI magic",
    description:
      "AI instantly generates professional designs based on your voice description.",
  },
  {
    number: "03",
    title: "Badlo",
    subtitle: "Refine by voice",
    description:
      '"Font badal do", "Thoda chhota karo" — speak naturally to edit.',
  },
  {
    number: "04",
    title: "Bhejo",
    subtitle: "Share anywhere",
    description:
      "Download or share directly on WhatsApp, Instagram, and more.",
  },
];

const HowItWorksSection = () => {
  return (
    <section className="py-24 px-6 gradient-warm-bg">
      <div className="container mx-auto max-w-5xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="font-heading text-4xl md:text-5xl font-bold mb-4">
            Kaise kaam karta hai?
          </h2>
          <p className="text-muted-foreground text-lg">
            Four simple steps. All by voice.
          </p>
        </motion.div>

        <div className="space-y-8">
          {steps.map((step, index) => (
            <motion.div
              key={step.number}
              initial={{ opacity: 0, x: index % 2 === 0 ? -30 : 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.15 }}
              className="flex items-start gap-6 rounded-2xl bg-card/80 backdrop-blur-sm p-8 shadow-card"
            >
              <span className="font-heading text-5xl font-bold gradient-text shrink-0">
                {step.number}
              </span>
              <div>
                <h3 className="font-heading text-2xl font-bold mb-1">
                  {step.title}{" "}
                  <span className="text-muted-foreground font-normal text-lg">
                    — {step.subtitle}
                  </span>
                </h3>
                <p className="text-muted-foreground text-lg italic">
                  {step.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default HowItWorksSection;
