import { motion } from 'framer-motion';
import { useAuthStore } from '@/store/authStore';
import { useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  FileText,
  AlertTriangle,
  BarChart3,
  Shield,
  LogOut,
  Clock,
  CheckCircle2,
  XCircle,
  TrendingUp,
  ScanLine,
  GitCompare,
  Play,
  Pause,
  Coffee,
  Activity,
  Timer,
  Brain,
  Eye,
  Zap,
  AlertCircle,
} from 'lucide-react';
import { BatchStats } from '@/types';
import { toast } from 'sonner';

interface SessionData {
  isActive: boolean;
  startTime: Date | null;
  totalDuration: number; // in seconds
  sheetsReviewed: number;
  breaksTime: number; // in seconds
  lastBreakTime: Date | null;
  fatigueLevel: 'fresh' | 'moderate' | 'tired' | 'exhausted';
  averageTimePerSheet: number; // in seconds
  accuracyRate: number;
  focusScore: number;
}

const AdminDashboard = () => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  
  // Session monitoring state
  const [session, setSession] = useState<SessionData>({
    isActive: false,
    startTime: null,
    totalDuration: 0,
    sheetsReviewed: 0,
    breaksTime: 0,
    lastBreakTime: null,
    fatigueLevel: 'fresh',
    averageTimePerSheet: 0,
    accuracyRate: 98.5,
    focusScore: 100,
  });
  
  const [isPaused, setIsPaused] = useState(false);
  const [showBreakReminder, setShowBreakReminder] = useState(false);

  // Timer effect
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    
    if (session.isActive && !isPaused) {
      interval = setInterval(() => {
        setSession(prev => {
          const newDuration = prev.totalDuration + 1;
          
          // Calculate fatigue level based on continuous work time
          const timeSinceBreak = prev.lastBreakTime 
            ? Math.floor((Date.now() - prev.lastBreakTime.getTime()) / 1000)
            : newDuration;
          
          let fatigueLevel: SessionData['fatigueLevel'] = 'fresh';
          let focusScore = 100;
          
          if (timeSinceBreak > 7200) { // 2+ hours
            fatigueLevel = 'exhausted';
            focusScore = 40;
          } else if (timeSinceBreak > 5400) { // 1.5+ hours
            fatigueLevel = 'tired';
            focusScore = 60;
          } else if (timeSinceBreak > 3600) { // 1+ hour
            fatigueLevel = 'moderate';
            focusScore = 80;
          }
          
          // Show break reminder every 45 minutes
          if (timeSinceBreak > 0 && timeSinceBreak % 2700 === 0) {
            setShowBreakReminder(true);
          }
          
          return {
            ...prev,
            totalDuration: newDuration,
            fatigueLevel,
            focusScore,
          };
        });
      }, 1000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [session.isActive, isPaused]);

  const handleLogout = () => {
    if (session.isActive) {
      toast.error('Please end your session before logging out');
      return;
    }
    logout();
    navigate('/');
  };

  const startSession = () => {
    setSession({
      isActive: true,
      startTime: new Date(),
      totalDuration: 0,
      sheetsReviewed: 0,
      breaksTime: 0,
      lastBreakTime: new Date(),
      fatigueLevel: 'fresh',
      averageTimePerSheet: 0,
      accuracyRate: 98.5,
      focusScore: 100,
    });
    setIsPaused(false);
    toast.success('Session started! Stay focused and take breaks when needed.');
  };

  const pauseSession = () => {
    setIsPaused(true);
    toast.info('Session paused. Take a break!');
  };

  const resumeSession = () => {
    setIsPaused(false);
    setSession(prev => ({
      ...prev,
      lastBreakTime: new Date(),
    }));
    setShowBreakReminder(false);
    toast.success('Session resumed. You got this!');
  };

  const endSession = () => {
    const summary = {
      duration: formatDuration(session.totalDuration),
      sheets: session.sheetsReviewed,
      avgTime: session.sheetsReviewed > 0 
        ? formatDuration(Math.floor(session.totalDuration / session.sheetsReviewed))
        : 'N/A',
    };
    
    setSession(prev => ({
      ...prev,
      isActive: false,
    }));
    
    toast.success(`Session ended! Duration: ${summary.duration}, Sheets: ${summary.sheets}`);
  };

  const takeBreak = () => {
    setIsPaused(true);
    setSession(prev => ({
      ...prev,
      lastBreakTime: new Date(),
    }));
    setShowBreakReminder(false);
    toast.info('Break started. Stretch, hydrate, and rest your eyes!');
  };

  const formatDuration = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hrs > 0) {
      return `${hrs}h ${mins}m`;
    }
    return `${mins}m ${secs}s`;
  };

  const getFatigueColor = (level: SessionData['fatigueLevel']) => {
    switch (level) {
      case 'fresh': return 'text-green-500 border-green-500';
      case 'moderate': return 'text-yellow-500 border-yellow-500';
      case 'tired': return 'text-orange-500 border-orange-500';
      case 'exhausted': return 'text-red-500 border-red-500';
    }
  };

  const getFatigueEmoji = (level: SessionData['fatigueLevel']) => {
    switch (level) {
      case 'fresh': return '😊';
      case 'moderate': return '😐';
      case 'tired': return '😓';
      case 'exhausted': return '😫';
    }
  };

  // Mock batch stats
  const batchStats: BatchStats = {
    totalSheets: 1250,
    sheetsProcessed: 980,
    pendingAnomalies: 47,
    avgConfidence: 94.2,
    etaMinutes: 45,
    releaseStatus: 'locked',
  };

  const cards = [
    {
      title: 'BATCH CREATION & ANSWER KEY',
      icon: FileText,
      description: 'Upload scans, manage answer keys with triple-entry AI validation',
      route: '/admin/batch-creation',
      color: 'border-foreground',
      badge: '3 Pending',
    },
    {
      title: 'OMR VERIFICATION',
      icon: ScanLine,
      description: 'AI-powered OMR detection with 3-pass voting and batch processing',
      route: '/admin/omr-verification',
      color: 'border-foreground',
      badge: 'AI Ready',
    },
    {
      title: 'ANSWER VERIFICATION',
      icon: GitCompare,
      description: '3-way tally: OMR Detection → AI Verification → Manual Entry comparison',
      route: '/admin/answer-verification',
      color: 'border-foreground',
      badge: 'Triple Check',
    },
    {
      title: 'ANOMALY REVIEW & VERIFICATION',
      icon: AlertTriangle,
      description: 'Review flagged sheets with AI confidence scores and human override',
      route: '/admin/anomaly-review',
      color: 'border-foreground',
      badge: `${batchStats.pendingAnomalies} Anomalies`,
    },
    {
      title: 'ANALYTICS & PUBLISHING',
      icon: BarChart3,
      description: 'Question-wise analytics, risk flags, and multi-sign result publishing',
      route: '/admin/analytics',
      color: 'border-foreground',
      badge: 'View Stats',
    },
    {
      title: 'BLOCKCHAIN AUDIT TRAIL',
      icon: Shield,
      description: 'Complete audit timeline with hash verification and export certificates',
      route: '/admin/blockchain',
      color: 'border-foreground',
      badge: '100% Verified',
    },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Break Reminder Modal */}
      {showBreakReminder && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-card border-4 border-yellow-500 p-8 max-w-md mx-4 shadow-2xl"
          >
            <div className="text-center">
              <Coffee className="w-16 h-16 mx-auto mb-4 text-yellow-500" />
              <h3 className="text-2xl font-bold mb-2">TIME FOR A BREAK!</h3>
              <p className="text-muted-foreground font-mono mb-6">
                You've been working for a while. Taking regular breaks improves accuracy and prevents fatigue.
              </p>
              <div className="flex gap-4 justify-center">
                <Button onClick={takeBreak} className="bg-yellow-500 hover:bg-yellow-600 text-black">
                  <Coffee className="w-4 h-4 mr-2" />
                  TAKE BREAK
                </Button>
                <Button variant="outline" onClick={() => setShowBreakReminder(false)} className="border-2">
                  CONTINUE
                </Button>
              </div>
            </div>
          </motion.div>
        </div>
      )}

      {/* Header */}
      <header className="border-b-4 border-foreground bg-card">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">EXAMNYX</h1>
              <p className="text-sm font-mono text-muted-foreground mt-1">ADMIN PORTAL</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right hidden sm:block">
                <p className="font-bold">{user?.name}</p>
                <div className="flex items-center gap-2 justify-end">
                  <Badge variant="outline" className="border-2 border-foreground text-xs">
                    {user?.role === 'institution_admin' ? 'INSTITUTION ADMIN' : 'EXAM CENTER'}
                  </Badge>
                </div>
              </div>
              <Button
                onClick={handleLogout}
                variant="outline"
                size="sm"
                className="border-2 border-foreground"
              >
                <LogOut className="w-4 h-4 mr-2" />
                LOGOUT
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Session Monitoring Card */}
      <section className="bg-muted/20 py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <Card className={`p-6 border-4 ${session.isActive ? 'border-green-500' : 'border-foreground'} shadow-lg`}>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                    session.isActive 
                      ? isPaused ? 'bg-yellow-500' : 'bg-green-500 animate-pulse' 
                      : 'bg-muted'
                  }`}>
                    {session.isActive ? (
                      isPaused ? <Pause className="w-6 h-6 text-white" /> : <Activity className="w-6 h-6 text-white" />
                    ) : (
                      <Play className="w-6 h-6" />
                    )}
                  </div>
                  <div>
                    <h3 className="text-xl font-bold">EVALUATION SESSION</h3>
                    <p className="text-sm font-mono text-muted-foreground">
                      {session.isActive 
                        ? isPaused ? 'SESSION PAUSED' : 'SESSION ACTIVE - Monitoring your work' 
                        : 'Start a session to track your evaluation work'}
                    </p>
                  </div>
                </div>
                
                <div className="flex gap-2">
                  {!session.isActive ? (
                    <Button onClick={startSession} className="bg-green-600 hover:bg-green-700">
                      <Play className="w-4 h-4 mr-2" />
                      START SESSION
                    </Button>
                  ) : (
                    <>
                      {isPaused ? (
                        <Button onClick={resumeSession} className="bg-green-600 hover:bg-green-700">
                          <Play className="w-4 h-4 mr-2" />
                          RESUME
                        </Button>
                      ) : (
                        <Button onClick={pauseSession} variant="outline" className="border-2 border-yellow-500 text-yellow-600">
                          <Pause className="w-4 h-4 mr-2" />
                          PAUSE
                        </Button>
                      )}
                      <Button onClick={takeBreak} variant="outline" className="border-2">
                        <Coffee className="w-4 h-4 mr-2" />
                        BREAK
                      </Button>
                      <Button onClick={endSession} variant="outline" className="border-2 border-red-500 text-red-600">
                        <XCircle className="w-4 h-4 mr-2" />
                        END
                      </Button>
                    </>
                  )}
                </div>
              </div>

              {/* Session Stats */}
              {session.isActive && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="grid grid-cols-2 md:grid-cols-5 gap-4 pt-4 border-t-2 border-muted"
                >
                  {/* Duration */}
                  <div className="text-center p-3 bg-muted/30 rounded-lg">
                    <Timer className="w-5 h-5 mx-auto mb-1 text-chart-2" />
                    <p className="text-2xl font-black">{formatDuration(session.totalDuration)}</p>
                    <p className="text-xs font-mono text-muted-foreground">DURATION</p>
                  </div>

                  {/* Sheets Reviewed */}
                  <div className="text-center p-3 bg-muted/30 rounded-lg">
                    <FileText className="w-5 h-5 mx-auto mb-1 text-chart-4" />
                    <p className="text-2xl font-black">{session.sheetsReviewed}</p>
                    <p className="text-xs font-mono text-muted-foreground">SHEETS REVIEWED</p>
                  </div>

                  {/* Focus Score */}
                  <div className="text-center p-3 bg-muted/30 rounded-lg">
                    <Eye className="w-5 h-5 mx-auto mb-1 text-blue-500" />
                    <p className="text-2xl font-black">{session.focusScore}%</p>
                    <p className="text-xs font-mono text-muted-foreground">FOCUS SCORE</p>
                  </div>

                  {/* Accuracy */}
                  <div className="text-center p-3 bg-muted/30 rounded-lg">
                    <Zap className="w-5 h-5 mx-auto mb-1 text-yellow-500" />
                    <p className="text-2xl font-black">{session.accuracyRate}%</p>
                    <p className="text-xs font-mono text-muted-foreground">ACCURACY</p>
                  </div>

                  {/* Fatigue Level */}
                  <div className={`text-center p-3 rounded-lg border-2 ${getFatigueColor(session.fatigueLevel)}`}>
                    <span className="text-2xl">{getFatigueEmoji(session.fatigueLevel)}</span>
                    <p className="text-lg font-black uppercase">{session.fatigueLevel}</p>
                    <p className="text-xs font-mono text-muted-foreground">FATIGUE LEVEL</p>
                  </div>
                </motion.div>
              )}

              {/* Fatigue Warning */}
              {session.isActive && (session.fatigueLevel === 'tired' || session.fatigueLevel === 'exhausted') && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className={`mt-4 p-3 rounded-lg flex items-center gap-3 ${
                    session.fatigueLevel === 'exhausted' ? 'bg-red-500/20 border-2 border-red-500' : 'bg-orange-500/20 border-2 border-orange-500'
                  }`}
                >
                  <AlertCircle className={`w-5 h-5 ${session.fatigueLevel === 'exhausted' ? 'text-red-500' : 'text-orange-500'}`} />
                  <div>
                    <p className="font-bold text-sm">
                      {session.fatigueLevel === 'exhausted' 
                        ? 'HIGH FATIGUE DETECTED - Please take a break immediately!' 
                        : 'Fatigue building up - Consider taking a short break soon'}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Working while fatigued can lead to errors and reduced accuracy
                    </p>
                  </div>
                  <Button size="sm" onClick={takeBreak} className={`ml-auto ${
                    session.fatigueLevel === 'exhausted' ? 'bg-red-500 hover:bg-red-600' : 'bg-orange-500 hover:bg-orange-600'
                  }`}>
                    <Coffee className="w-4 h-4 mr-1" />
                    BREAK NOW
                  </Button>
                </motion.div>
              )}
            </Card>
          </motion.div>
        </div>
      </section>

      {/* KPI Strip */}
      <section className="border-b-4 border-foreground bg-card py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h3 className="text-lg font-bold mb-4 font-mono">LIVE BATCH OVERVIEW</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1 }}
              className="border-4 border-foreground bg-background p-4 shadow-md"
            >
              <div className="text-3xl font-bold mb-1">{batchStats.totalSheets}</div>
              <div className="text-xs font-mono text-muted-foreground">TOTAL SHEETS</div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 }}
              className="border-4 border-foreground bg-background p-4 shadow-md"
            >
              <div className="flex items-center gap-2 mb-1">
                <CheckCircle2 className="w-5 h-5 text-green-500" />
                <div className="text-3xl font-bold">{batchStats.sheetsProcessed}</div>
              </div>
              <div className="text-xs font-mono text-muted-foreground">PROCESSED</div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.3 }}
              className="border-4 border-foreground bg-background p-4 shadow-md"
            >
              <div className="flex items-center gap-2 mb-1">
                <AlertTriangle className="w-5 h-5 text-yellow-500" />
                <div className="text-3xl font-bold">{batchStats.pendingAnomalies}</div>
              </div>
              <div className="text-xs font-mono text-muted-foreground">ANOMALIES</div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.4 }}
              className="border-4 border-foreground bg-background p-4 shadow-md"
            >
              <div className="flex items-center gap-2 mb-1">
                <TrendingUp className="w-5 h-5 text-blue-500" />
                <div className="text-3xl font-bold">{batchStats.avgConfidence}%</div>
              </div>
              <div className="text-xs font-mono text-muted-foreground">AVG CONFIDENCE</div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.5 }}
              className="border-4 border-foreground bg-background p-4 shadow-md"
            >
              <div className="flex items-center gap-2 mb-1">
                <Clock className="w-5 h-5" />
                <div className="text-3xl font-bold">{batchStats.etaMinutes}m</div>
              </div>
              <div className="text-xs font-mono text-muted-foreground">TIME REMAINING</div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Main Cards */}
      <section className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h3 className="text-2xl font-bold mb-6">ADMIN ACTIONS</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {cards.map((card, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                whileHover={{ y: -8 }}
              >
                <Card
                  className={`p-8 border-4 ${card.color} shadow-lg hover:shadow-2xl transition-all cursor-pointer h-full`}
                  onClick={() => navigate(card.route)}
                >
                  <div className="flex items-start justify-between mb-6">
                    <div className="w-16 h-16 border-4 border-foreground bg-background flex items-center justify-center">
                      <card.icon className="w-8 h-8" />
                    </div>
                    <Badge variant="outline" className="border-2 border-foreground">
                      {card.badge}
                    </Badge>
                  </div>
                  <h3 className="text-2xl font-bold mb-3">{card.title}</h3>
                  <p className="text-muted-foreground font-mono text-sm leading-relaxed">
                    {card.description}
                  </p>
                  <div className="mt-6">
                    <Button
                      className="border-2 border-foreground shadow-sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(card.route);
                      }}
                    >
                      OPEN
                    </Button>
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
};

export default AdminDashboard;
