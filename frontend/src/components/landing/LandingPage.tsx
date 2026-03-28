import { useRef } from "react";
import { useNavigate } from "react-router-dom";
import { motion, useInView } from "framer-motion";
import { Shield, FileCheck, Sparkles, ArrowRight, CloudUpload, Brain, CheckCircle } from "lucide-react";
import { Button } from "../ui/button";

function FadeInSection({ children, className = "", delay = 0 }: { children: React.ReactNode; className?: string; delay?: number }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.5, delay, ease: [0.4, 0, 0.2, 1] as [number, number, number, number] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

export function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-white text-[#0F172A]">
      {/* Nav */}
      <nav className="fixed top-0 w-full z-50 glass border-b border-white/20 shadow-sm">
        <div className="flex justify-between items-center px-6 py-4 max-w-7xl mx-auto">
          <span className="text-xl font-bold tracking-tight text-[#0D9488]">
            Antechamber Health
          </span>
          <div className="hidden md:flex items-center gap-8">
            <a href="#how-it-works" className="text-sm font-medium text-[#64748B] hover:text-[#0D9488] transition-colors">How It Works</a>
            <a href="#features" className="text-sm font-medium text-[#64748B] hover:text-[#0D9488] transition-colors">Features</a>
            <a href="#benefits" className="text-sm font-medium text-[#64748B] hover:text-[#0D9488] transition-colors">Benefits</a>
          </div>
          <Button onClick={() => navigate("/queue")}>
            Request Demo
          </Button>
        </div>
      </nav>

      {/* Hero */}
      <header className="relative min-h-screen flex items-center pt-20 hero-gradient overflow-hidden">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left */}
          <div className="lg:col-span-7 z-10">
            <div className="inline-flex items-center px-3 py-1 rounded-full bg-[#0D9488]/10 text-[#0D9488] text-[11px] uppercase tracking-wider font-semibold mb-6">
              <span className="mr-2 h-1.5 w-1.5 rounded-full bg-[#0D9488] pulse-dot" />
              AI-Powered Referral Triage
            </div>
            <h1 className="text-5xl lg:text-7xl font-bold text-[#0F172A] leading-[1.1] mb-6">
              Every referral, triaged in{" "}
              <span className="text-[#0D9488] italic">seconds.</span>
            </h1>
            <p className="text-lg lg:text-xl text-[#64748B] leading-relaxed mb-10 max-w-xl">
              Antechamber Health parses referral notes and connects to your Health Information Exchange.
              We give your team a complete patient picture, so you're prepared before the first appointment.
            </p>
            <div className="flex flex-wrap gap-4 mb-12">
              <Button size="lg" className="shadow-lg shadow-[#0D9488]/20" onClick={() => navigate("/queue")}>
                Request Demo
                <ArrowRight className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="lg" onClick={() => {
                document.getElementById("how-it-works")?.scrollIntoView({ behavior: "smooth" });
              }}>
                See How It Works
              </Button>
            </div>
            <div className="flex items-center gap-6 text-[#64748B]/60 text-[11px] uppercase tracking-[0.1em] font-semibold">
              <span className="flex items-center gap-1.5"><Shield className="h-3 w-3" /> HIPAA Compliant</span>
              <span className="h-1 w-1 rounded-full bg-slate-300" />
              <span>BAA Available</span>
              <span className="h-1 w-1 rounded-full bg-slate-300" />
              <span>SOC 2 In Progress</span>
            </div>
          </div>

          {/* Right — floating mockup */}
          <div className="lg:col-span-5 relative">
            <div className="floating glass rounded-xl overflow-hidden shadow-2xl border border-white/40">
              <div className="bg-slate-50 px-4 py-2 flex items-center gap-2 border-b border-slate-200/50">
                <div className="flex gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-400/40" />
                  <div className="w-2.5 h-2.5 rounded-full bg-amber-400/40" />
                  <div className="w-2.5 h-2.5 rounded-full bg-green-400/40" />
                </div>
                <div className="mx-auto bg-slate-100 px-4 py-1 rounded text-[10px] text-[#64748B]/50 font-mono">
                  app.antechamber.health/review
                </div>
              </div>
              <div className="bg-gradient-to-br from-[#FFF8F0] to-[#F5F0FF] p-6 min-h-[300px] flex items-center justify-center">
                <div className="space-y-3 w-full max-w-sm">
                  <div className="glass p-3 rounded-lg shadow-sm flex justify-between items-center">
                    <span className="font-bold text-sm">Patient Review</span>
                    <span className="px-2 py-0.5 bg-[#0D9488] text-white text-[10px] rounded-full font-bold">ROUTINE</span>
                  </div>
                  <div className="glass p-3 rounded-lg shadow-sm flex justify-between items-center">
                    <span className="font-bold text-sm">AI Summary</span>
                    <Sparkles className="h-4 w-4 text-[#0D9488]" />
                  </div>
                  <div className="glass p-3 rounded-lg shadow-sm flex justify-between items-center">
                    <span className="font-bold text-sm">Clinical Data</span>
                    <span className="text-xs text-[#64748B]">12 sections</span>
                  </div>
                </div>
              </div>
            </div>
            <div className="absolute -z-10 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[140%] h-[140%] bg-[#0D9488]/5 blur-[100px] rounded-full" />
          </div>
        </div>
      </header>

      {/* How It Works */}
      <section id="how-it-works" className="py-24 relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">Precision Workflow</h2>
            <div className="h-1 w-12 bg-[#0D9488] mx-auto rounded-full" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { icon: CloudUpload, step: "01", title: "Upload or receive", desc: "Securely ingest PDFs, faxes, or EMR exports. Our AI handles the mess so your team doesn't have to." },
              { icon: Brain, step: "02", title: "AI extracts & triages", desc: "Proprietary LLMs extract comorbidities, ICD-10 codes, and clinical urgency based on your specific protocols." },
              { icon: CheckCircle, step: "03", title: "Review and act", desc: "Approve the triage, schedule the patient, or request missing data with a single click. Efficiency redefined." },
            ].map((item, i) => (
              <FadeInSection key={i} delay={i * 0.15}>
                <div className="glass p-8 rounded-xl relative group hover:-translate-y-2 transition-transform duration-300">
                  <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-[#0D9488] to-transparent rounded-t-xl opacity-0 group-hover:opacity-100 transition-opacity" />
                  <div className="w-12 h-12 rounded-lg bg-[#0D9488]/10 flex items-center justify-center text-[#0D9488] mb-6">
                    <item.icon className="h-6 w-6" />
                  </div>
                  <div className="text-[11px] uppercase tracking-widest text-[#0D9488]/50 mb-2 font-semibold">Step {item.step}</div>
                  <h3 className="text-xl font-bold mb-3">{item.title}</h3>
                  <p className="text-[#64748B] text-sm leading-relaxed">{item.desc}</p>
                </div>
              </FadeInSection>
            ))}
          </div>
        </div>
      </section>

      {/* Feature Showcase */}
      <section id="features" className="py-24 bg-slate-50/50 relative">
        <div className="max-w-7xl mx-auto px-6">
          <div className="max-w-2xl mb-16">
            <h2 className="text-4xl font-bold mb-6">Built for the Clinical Workspace</h2>
            <p className="text-[#64748B] text-lg">Stop fighting your EMR. Start reviewing referrals in a workspace designed for speed and clarity.</p>
          </div>
          <FadeInSection>
            <div className="relative glass rounded-xl p-4 shadow-2xl border border-white/40">
              <div className="bg-gradient-to-br from-[#FFF8F0] to-[#F5F0FF] rounded-lg p-12 min-h-[400px] flex items-center justify-center">
                <div className="grid grid-cols-3 gap-6 w-full max-w-3xl">
                  <div className="glass p-4 rounded-lg shadow-sm col-span-1">
                    <div className="flex items-center gap-2 mb-2">
                      <Sparkles className="h-4 w-4 text-[#0D9488]" />
                      <span className="text-[10px] font-bold uppercase text-[#0D9488]">AI Summary</span>
                    </div>
                    <div className="space-y-2">
                      <div className="h-2 bg-slate-200 rounded w-full" />
                      <div className="h-2 bg-slate-200 rounded w-3/4" />
                      <div className="h-2 bg-slate-200 rounded w-5/6" />
                    </div>
                  </div>
                  <div className="glass p-4 rounded-lg shadow-sm col-span-2">
                    <div className="flex items-center gap-2 mb-3">
                      <FileCheck className="h-4 w-4 text-[#64748B]" />
                      <span className="text-[10px] font-bold uppercase text-[#64748B]">Clinical Data</span>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="bg-slate-50 p-2 rounded"><div className="h-2 bg-slate-200 rounded w-2/3" /></div>
                      <div className="bg-slate-50 p-2 rounded"><div className="h-2 bg-slate-200 rounded w-1/2" /></div>
                      <div className="bg-red-50 p-2 rounded border-l-2 border-red-300"><div className="h-2 bg-red-200 rounded w-3/4" /></div>
                      <div className="bg-slate-50 p-2 rounded"><div className="h-2 bg-slate-200 rounded w-4/5" /></div>
                    </div>
                  </div>
                </div>
              </div>
              {/* Floating annotations */}
              <div className="absolute top-[20%] right-[8%] glass px-4 py-3 rounded-lg shadow-xl border-l-4 border-[#0D9488]">
                <div className="flex items-center gap-3">
                  <Sparkles className="h-4 w-4 text-[#0D9488]" />
                  <div>
                    <p className="text-[10px] uppercase tracking-widest text-[#0D9488] font-bold">AI Summary</p>
                    <p className="text-sm font-semibold">Instant clinical context</p>
                  </div>
                </div>
              </div>
              <div className="absolute bottom-[25%] left-[5%] glass px-4 py-3 rounded-lg shadow-xl border-l-4 border-[#DC2626]">
                <div className="flex items-center gap-3">
                  <Shield className="h-4 w-4 text-[#DC2626]" />
                  <div>
                    <p className="text-[10px] uppercase tracking-widest text-[#DC2626] font-bold">Urgent Triage</p>
                    <p className="text-sm font-semibold">Flagged for immediate review</p>
                  </div>
                </div>
              </div>
            </div>
          </FadeInSection>
        </div>
      </section>

      {/* Benefits */}
      <section id="benefits" className="py-24">
        <div className="max-w-7xl mx-auto px-6 space-y-32">
          {[
            { title: "Built for referral coordinators, not clinicians.", desc: "Most tools are built for the physician's eye. We built Antechamber for the operations team that keeps the clinic running. Large buttons, clear status indicators, and bulk actions.", tags: ["Bulk Intake", "Priority Sorter", "Fax Ingestion"], reverse: false },
            { title: "Every format, one workflow.", desc: "Whether it's a blurry handwritten fax, a multi-page PDF export, or a direct HL7 message, Antechamber normalizes the data into a single, clean view for your intake team.", tags: ["PDF", "Fax", "HL7", "CDA"], reverse: true },
            { title: "Your data becomes your advantage.", desc: "Every correction your team makes teaches the AI. Over time, your triage becomes perfectly aligned with your clinic's unique clinical guidelines and scheduling logic.", tags: ["Feedback Loop", "Adaptive Learning", "Custom Protocols"], reverse: false },
          ].map((row, i) => (
            <FadeInSection key={i}>
              <div className={`grid grid-cols-1 lg:grid-cols-2 gap-16 items-center`}>
                <div className={row.reverse ? "order-2 lg:order-2" : ""}>
                  <h3 className="text-3xl font-bold mb-6">{row.title}</h3>
                  <p className="text-[#64748B] leading-relaxed mb-8">{row.desc}</p>
                  <div className="flex flex-wrap gap-3">
                    {row.tags.map((tag) => (
                      <span key={tag} className="px-4 py-2 glass rounded-lg text-xs font-semibold text-[#0D9488]">{tag}</span>
                    ))}
                  </div>
                </div>
                <div className={`glass p-8 rounded-xl bg-gradient-to-br from-slate-50 to-white min-h-[250px] flex items-center justify-center ${row.reverse ? "order-1 lg:order-1" : ""}`}>
                  <div className="w-full max-w-sm space-y-3">
                    <div className="h-3 bg-[#0D9488]/10 rounded-full overflow-hidden">
                      <div className="h-full bg-[#0D9488] rounded-full" style={{ width: `${65 + i * 12}%` }} />
                    </div>
                    <p className="text-xs text-[#64748B] italic text-center">
                      {i === 0 && "85% faster triage processing"}
                      {i === 1 && "All formats, unified view"}
                      {i === 2 && "98% extraction accuracy"}
                    </p>
                  </div>
                </div>
              </div>
            </FadeInSection>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6 relative overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[80%] h-[80%] bg-[#0D9488]/5 blur-[120px] rounded-full" />
        <div className="max-w-5xl mx-auto glass p-16 rounded-[2rem] text-center relative z-10">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Ready to transform your referral workflow?
          </h2>
          <p className="text-[#64748B] text-lg max-w-2xl mx-auto mb-12">
            Join modern clinical teams reducing triage time by 85% and improving patient access.
          </p>
          <div className="flex flex-col sm:flex-row justify-center items-center gap-6">
            <Button size="lg" className="shadow-xl shadow-[#0D9488]/30 text-lg px-10 py-5 h-auto" onClick={() => navigate("/queue")}>
              Request Demo
            </Button>
            <Button variant="outline" size="lg" className="text-lg px-10 py-5 h-auto">
              Contact Sales
            </Button>
          </div>
          <p className="mt-6 text-sm text-[#64748B]">Free pilot for early partners</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-50/50 w-full py-12 px-6 border-t border-[#0D9488]/5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-7xl mx-auto">
          <div>
            <div className="text-lg font-bold text-[#0F172A] mb-4">Antechamber Health</div>
            <p className="text-xs tracking-wide uppercase text-[#64748B]/70 max-w-xs leading-loose">
              &copy; 2025 Antechamber Health. Precision Triage for Modern Clinicians.
            </p>
          </div>
          <div className="flex flex-wrap gap-x-12 gap-y-6 md:justify-end">
            {["About", "Privacy", "Terms", "Contact"].map((link) => (
              <a key={link} href="#" className="text-xs tracking-wide uppercase text-[#64748B]/70 hover:text-[#0D9488] transition-colors">
                {link}
              </a>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
