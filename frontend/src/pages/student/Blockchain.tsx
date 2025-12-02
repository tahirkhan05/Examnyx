import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Shield, CheckCircle2, Lock, FileText, Scan, Brain, UserCheck, Award, Clock, Package } from 'lucide-react';

interface ProcessingStep {
  id: string;
  title: string;
  description: string;
  timestamp: string;
  status: 'completed' | 'current' | 'pending';
  icon: React.ElementType;
  blockHash?: string;
  details?: string;
}

const Blockchain = () => {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Mock processing timeline - like delivery status
  const processingSteps: ProcessingStep[] = [
    {
      id: '1',
      title: 'ANSWER SHEET RECEIVED',
      description: 'Your OMR sheet was scanned and uploaded to the system',
      timestamp: '2024-11-20T09:15:32Z',
      status: 'completed',
      icon: Scan,
      blockHash: '0x7f9fade1c0d57a7af66ab4ead79c2eb7',
      details: 'Sheet ID: OMR_2024_CS_MID_001'
    },
    {
      id: '2',
      title: 'BUBBLE DETECTION COMPLETE',
      description: 'AI analyzed your marked answers with 98.5% confidence',
      timestamp: '2024-11-20T09:16:45Z',
      status: 'completed',
      icon: Brain,
      blockHash: '0x3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f',
      details: '50 questions detected • All bubbles verified'
    },
    {
      id: '3',
      title: 'ANSWER KEY MATCHED',
      description: 'Your answers were compared against the locked answer key',
      timestamp: '2024-11-20T09:18:20Z',
      status: 'completed',
      icon: FileText,
      blockHash: '0x9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d',
      details: 'Answer key verified on blockchain • Tamper-proof'
    },
    {
      id: '4',
      title: 'SCORE CALCULATED',
      description: 'Your marks were computed using the verified scoring rules',
      timestamp: '2024-11-20T09:19:05Z',
      status: 'completed',
      icon: Award,
      blockHash: '0xe5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0',
      details: 'Total: 42/50 • Percentage: 84%'
    },
    {
      id: '5',
      title: 'HUMAN VERIFICATION',
      description: 'Result verified by authorized evaluator',
      timestamp: '2024-11-20T10:45:30Z',
      status: 'completed',
      icon: UserCheck,
      blockHash: '0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d',
      details: 'Verified by: Dr. Smith • Signature recorded'
    },
    {
      id: '6',
      title: 'RESULT FINALIZED',
      description: 'Your result is now permanently recorded on blockchain',
      timestamp: '2024-11-20T10:47:15Z',
      status: 'completed',
      icon: Shield,
      blockHash: '0x7f9fade1c0d57a7af66ab4ead7c2eb2b',
      details: 'Block #12458 • Immutable record created'
    },
  ];

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return {
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
      time: date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true })
    };
  };

  const getTimeDifference = (timestamp: string) => {
    const then = new Date(timestamp).getTime();
    const now = currentTime.getTime();
    const diff = now - then;
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
    if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    return 'Just now';
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b-4 border-foreground bg-card">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Link to="/student/dashboard">
            <Button variant="outline" size="sm" className="mb-4 border-2 border-foreground">
              <ArrowLeft className="w-4 h-4 mr-2" />
              BACK TO DASHBOARD
            </Button>
          </Link>
          <div className="flex items-center gap-3">
            <Package className="w-8 h-8" />
            <div>
              <h1 className="text-4xl font-bold">BLOCKCHAIN AUDIT</h1>
              <p className="text-sm font-mono text-muted-foreground mt-1">
                Track your result processing - Every step secured & verified
              </p>
            </div>
          </div>
        </div>
      </header>

      <section className="py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Status Summary */}
            <Card className="p-6 border-4 border-green-500 bg-green-50 dark:bg-green-950/20 shadow-lg">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-full bg-green-500 flex items-center justify-center">
                  <CheckCircle2 className="w-8 h-8 text-white" />
                </div>
                <div className="flex-1">
                  <h2 className="text-2xl font-bold text-green-700 dark:text-green-400">RESULT DELIVERED & SECURED</h2>
                  <p className="text-sm text-green-600 dark:text-green-500 font-mono">
                    All 6 processing steps completed • Your data is tamper-proof
                  </p>
                </div>
                <Badge className="bg-green-500 text-white border-0 text-lg px-4 py-2">
                  ✓ VERIFIED
                </Badge>
              </div>
            </Card>

            {/* Processing Timeline - Like Delivery Status */}
            <Card className="p-6 border-4 border-foreground shadow-lg">
              <div className="flex items-center gap-2 mb-6">
                <Clock className="w-5 h-5" />
                <h3 className="text-xl font-bold">PROCESSING TIMELINE</h3>
                <span className="ml-auto text-xs font-mono text-muted-foreground">
                  Live tracking • Blockchain secured
                </span>
              </div>

              <div className="relative">
                {processingSteps.map((step, index) => {
                  const IconComponent = step.icon;
                  const time = formatTimestamp(step.timestamp);
                  const isLast = index === processingSteps.length - 1;
                  
                  return (
                    <motion.div
                      key={step.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="relative pl-12 pb-8"
                    >
                      {/* Vertical Line */}
                      {!isLast && (
                        <div className="absolute left-[18px] top-10 w-0.5 h-full bg-green-500" />
                      )}
                      
                      {/* Step Icon */}
                      <div className={`absolute left-0 w-9 h-9 rounded-full flex items-center justify-center border-2 ${
                        step.status === 'completed' 
                          ? 'bg-green-500 border-green-500 text-white' 
                          : step.status === 'current'
                          ? 'bg-blue-500 border-blue-500 text-white animate-pulse'
                          : 'bg-muted border-muted-foreground text-muted-foreground'
                      }`}>
                        {step.status === 'completed' ? (
                          <CheckCircle2 className="w-5 h-5" />
                        ) : (
                          <IconComponent className="w-4 h-4" />
                        )}
                      </div>

                      {/* Step Content */}
                      <div className={`border-2 rounded-lg p-4 ${
                        step.status === 'completed' 
                          ? 'border-green-500 bg-green-50/50 dark:bg-green-950/10' 
                          : step.status === 'current'
                          ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-950/10'
                          : 'border-muted bg-muted/20'
                      }`}>
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <IconComponent className="w-4 h-4" />
                              <h4 className="font-bold">{step.title}</h4>
                              {step.status === 'completed' && (
                                <Badge variant="outline" className="text-xs border-green-500 text-green-600">
                                  ✓ DONE
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm text-muted-foreground mb-2">{step.description}</p>
                            {step.details && (
                              <p className="text-xs font-mono text-muted-foreground bg-muted/50 px-2 py-1 rounded inline-block">
                                {step.details}
                              </p>
                            )}
                          </div>
                          <div className="text-right flex-shrink-0">
                            <p className="text-sm font-bold">{time.date}</p>
                            <p className="text-xs font-mono text-muted-foreground">{time.time}</p>
                            <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                              {getTimeDifference(step.timestamp)}
                            </p>
                          </div>
                        </div>
                        
                        {/* Block Hash */}
                        {step.blockHash && (
                          <div className="mt-3 pt-3 border-t border-muted">
                            <div className="flex items-center gap-2">
                              <Lock className="w-3 h-3 text-muted-foreground" />
                              <span className="text-xs font-mono text-muted-foreground">
                                Block: {step.blockHash.substring(0, 20)}...
                              </span>
                              <Badge variant="secondary" className="text-xs ml-auto">
                                <Shield className="w-3 h-3 mr-1" />
                                IMMUTABLE
                              </Badge>
                            </div>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </Card>

            {/* Security Assurance */}
            <Card className="p-6 border-4 border-chart-4 shadow-lg">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Shield className="w-5 h-5" />
                WHY YOUR DATA IS SAFE
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-start gap-3 p-3 bg-muted/30 rounded-lg">
                  <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-bold text-sm">Immutable Records</p>
                    <p className="text-xs text-muted-foreground">Once recorded, data cannot be changed or deleted</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 bg-muted/30 rounded-lg">
                  <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-bold text-sm">Cryptographic Hashing</p>
                    <p className="text-xs text-muted-foreground">SHA-256 encryption protects every block</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 bg-muted/30 rounded-lg">
                  <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-bold text-sm">Chain Verification</p>
                    <p className="text-xs text-muted-foreground">Each block links to previous - tampering breaks the chain</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 bg-muted/30 rounded-lg">
                  <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-bold text-sm">Multi-Signature Approval</p>
                    <p className="text-xs text-muted-foreground">AI + Human + Admin verification required</p>
                  </div>
                </div>
              </div>
            </Card>

            {/* Final Block Details */}
            <Card className="p-6 border-4 border-chart-1 shadow-lg">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Lock className="w-5 h-5" />
                YOUR RESULT BLOCK
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-muted/30 rounded-lg">
                  <span className="font-mono text-sm">Block Index</span>
                  <span className="font-bold">#12458</span>
                </div>
                <div className="p-3 bg-muted/30 rounded-lg">
                  <span className="font-mono text-sm block mb-1">Block Hash</span>
                  <span className="font-mono text-xs break-all text-muted-foreground">
                    0x7f9fade1c0d57a7af66ab4ead7c2eb2b9a0eb0d3a5a3b1d2c4e5f6a7b8c9d0e1
                  </span>
                </div>
                <div className="p-3 bg-muted/30 rounded-lg">
                  <span className="font-mono text-sm block mb-1">Previous Hash</span>
                  <span className="font-mono text-xs break-all text-muted-foreground">
                    0x3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d
                  </span>
                </div>
              </div>
            </Card>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default Blockchain;
