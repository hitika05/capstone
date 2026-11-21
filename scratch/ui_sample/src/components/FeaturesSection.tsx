import { motion } from "framer-motion";
import { Mic, Palette, MessageSquare, Database, Globe, Share2 } from "lucide-react";

const features = [
  {
    icon: Mic,
    title: "Voice-First Design",
    description:
      "Speak in Hindi or Marathi to create designs. No typing, no English needed.",
  },
  {
    icon: Palette,
    title: "AI Visual Generation",
    description:
      "Generate logos, Instagram posts, flyers and price lists from your voice.",
  },
  {
    icon: MessageSquare,
    title: "Conversational Editing",
    description:
      '"Logo motha kar", "Background badal" — refine designs naturally.',
  },
  {
    icon: Database,
    title: "Brand Memory",
    description:
      "Stores your logo, colors & fonts. Consistent branding, automatically.",
  },
  {
    icon: Globe,
    title: "Multilingual AI",
    description:
      "Handles Marathi, Hindi & code-switching seamlessly with optimized STT.",
  },
  {
    icon: Share2,
    title: "Export & Share",
    description:
      "Download to gallery or share directly via WhatsApp & social media.",
  },
];

const FeaturesSection = () => {
  return (
    <section className="py-24 px-6">
      <div className="container mx-auto max-w-6xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="font-heading text-4xl md:text-5xl font-bold mb-4">
            Design ka naya tarika
          </h2>
          <p className="text-muted-foreground text-lg max-w-xl mx-auto">
            Every feature crafted for micro-entrepreneurs who think in their
            mother tongue.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="group rounded-2xl border border-border bg-card p-8 shadow-card transition-all hover:shadow-elevated hover:-translate-y-1"
            >
              <div className="mb-5 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                <feature.icon className="h-6 w-6" />
              </div>
              <h3 className="font-heading text-xl font-semibold mb-2">
                {feature.title}
              </h3>
              <p className="text-muted-foreground leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FeaturesSection;
