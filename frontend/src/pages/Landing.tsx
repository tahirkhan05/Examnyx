import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Shield, Cpu, Lock, CheckCircle2, Zap, Users } from 'lucide-react';
import heroImage from '@/assets/hero-omr.jpg';

const Landing = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: Cpu,
      title: 'AI-Powered Verification',
      description: 'Advanced AI algorithms verify answer keys and detect anomalies with 99.8% accuracy',
    },
    {
      icon: Shield,
      title: 'Blockchain-Backed Audit Trail',
      description: 'Immutable blockchain records ensure complete transparency and data integrity',
    },
    {
      icon: Zap,
      title: 'Smart OMR Recovery',
      description: 'Damaged sheets are automatically reconstructed using AI-powered quality assessment',
    },
    {
      icon: CheckCircle2,
      title: 'Automated Evaluation',
      description: 'Bubble detection and mark calculation with human-in-the-loop verification',
    },
    {
      icon: Lock,
      title: 'Secure & Tamper-Proof',
      description: 'Multi-level approval system with cryptographic hash verification',
    },
    {
      icon: Users,
      title: 'Role-Based Access',
      description: 'Granular permissions for students, evaluators, and administrators',
    },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center px-4 sm:px-6 lg:px-8 border-b-4 border-foreground overflow-hidden">
        <div className="absolute inset-0 z-0">
          <img
            src={heroImage}
            alt="OMR scanning visualization"
            className="w-full h-full object-cover opacity-20"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-background/80 via-background/60 to-background" />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="max-w-5xl mx-auto text-center relative z-10"
        >
          <motion.div
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.5 }}
            className="inline-block px-4 py-2 mb-6 border-4 border-foreground bg-background"
          >
            <span className="text-sm font-mono font-bold tracking-wider">NEXT-GEN OMR EVALUATION</span>
          </motion.div>

          <h1 className="text-6xl sm:text-7xl lg:text-8xl font-bold mb-8 tracking-tight">
            EXAMNYX
          </h1>

          <p className="text-xl sm:text-2xl mb-12 max-w-3xl mx-auto font-mono">
            AI-powered, blockchain-backed OMR evaluation system that ensures accuracy, transparency, and trust in every assessment.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button
              size="lg"
              onClick={() => navigate('/student/login')}
              className="w-full sm:w-auto text-lg px-8 py-6 border-4 border-foreground shadow-xl hover:shadow-2xl transition-shadow"
            >
              STUDENT PORTAL
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={() => navigate('/admin/login')}
              className="w-full sm:w-auto text-lg px-8 py-6 border-4 border-foreground shadow-xl hover:shadow-2xl transition-shadow"
            >
              ADMIN PORTAL
            </Button>
          </div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1, duration: 1 }}
            className="mt-16 flex justify-center items-center gap-8 text-sm font-mono"
          >
            <div className="text-center">
              <div className="text-3xl font-bold">99.8%</div>
              <div className="text-muted-foreground">Accuracy</div>
            </div>
            <div className="w-px h-12 bg-foreground" />
            <div className="text-center">
              <div className="text-3xl font-bold">10K+</div>
              <div className="text-muted-foreground">Sheets/Day</div>
            </div>
            <div className="w-px h-12 bg-foreground" />
            <div className="text-center">
              <div className="text-3xl font-bold">100%</div>
              <div className="text-muted-foreground">Transparent</div>
            </div>
          </motion.div>
        </motion.div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 border-b-4 border-foreground">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-5xl font-bold mb-6">FEATURES</h2>
            <p className="text-xl text-muted-foreground font-mono max-w-2xl mx-auto">
              Built with cutting-edge technology for the modern education ecosystem
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                whileHover={{ y: -8 }}
                className="border-4 border-foreground bg-card p-8 shadow-md hover:shadow-2xl transition-all"
              >
                <div className="mb-4">
                  <div className="w-16 h-16 border-4 border-foreground bg-background flex items-center justify-center">
                    <feature.icon className="w-8 h-8" />
                  </div>
                </div>
                <h3 className="text-2xl font-bold mb-3">{feature.title}</h3>
                <p className="text-muted-foreground font-mono text-sm leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="max-w-4xl mx-auto text-center border-4 border-foreground bg-card p-12 shadow-2xl"
        >
          <h2 className="text-4xl sm:text-5xl font-bold mb-6">
            READY TO GET STARTED?
          </h2>
          <p className="text-xl text-muted-foreground font-mono mb-8">
            Experience the future of OMR evaluation today
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              size="lg"
              onClick={() => navigate('/student/login')}
              className="text-lg px-8 py-6 border-4 border-foreground shadow-xl"
            >
              STUDENT LOGIN
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={() => navigate('/admin/login')}
              className="text-lg px-8 py-6 border-4 border-foreground shadow-xl"
            >
              ADMIN LOGIN
            </Button>
          </div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="border-t-4 border-foreground py-8 px-4">
        <div className="max-w-7xl mx-auto text-center text-muted-foreground font-mono text-sm">
          <p>&copy; 2025 EXAMNYX. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
