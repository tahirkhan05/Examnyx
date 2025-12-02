import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { 
  ArrowLeft, CheckCircle2, Loader2, ScanLine, Brain, 
  UserCheck, Shield, AlertTriangle, Eye, EyeOff,
  ChevronRight, RefreshCw, Lock, Sparkles, FileText,
  Check, X, Minus, Download, Upload, Calculator
} from 'lucide-react';
import { toast } from 'sonner';
import apiService from '@/services/api.service';

interface QuestionAnswer {
  questionNumber: number;
  omrDetected: string | null;       // From OMR sheet scan
  aiVerified: string | null;        // AI's solution
  manualEntry: string | null;       // Manually entered
  omrConfidence: number;
  aiConfidence: number;
  omrAiMatch: boolean | null;       // OMR vs AI match
  aiManualMatch: boolean | null;    // AI vs Manual match
  finalAnswer: string | null;       // Final verified answer
  status: 'pending' | 'matched' | 'mismatch' | 'review';
  notes?: string;
}

interface VerificationStats {
  totalQuestions: number;
  omrDetected: number;
  aiVerified: number;
  manualEntered: number;
  allMatched: number;
  mismatches: number;
  pendingReview: number;
}

const AnswerVerification = () => {
  const [sheetId, setSheetId] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentPhase, setCurrentPhase] = useState<'idle' | 'omr' | 'ai' | 'manual' | 'complete'>('idle');
  const [answers, setAnswers] = useState<QuestionAnswer[]>([]);
  const [showOnlyMismatches, setShowOnlyMismatches] = useState(false);
  const [expandedQuestion, setExpandedQuestion] = useState<number | null>(null);

  const totalQuestions = 50;
  const options = ['A', 'B', 'C', 'D'];

  // Calculate stats
  const stats: VerificationStats = {
    totalQuestions: answers.length,
    omrDetected: answers.filter(a => a.omrDetected).length,
    aiVerified: answers.filter(a => a.aiVerified).length,
    manualEntered: answers.filter(a => a.manualEntry).length,
    allMatched: answers.filter(a => a.status === 'matched').length,
    mismatches: answers.filter(a => a.status === 'mismatch').length,
    pendingReview: answers.filter(a => a.status === 'review' || a.status === 'pending').length,
  };

  // Phase 1: OMR Detection
  const runOMRDetection = async () => {
    setIsLoading(true);
    setCurrentPhase('omr');
    toast.loading('Running OMR Detection...', { id: 'omr' });

    // Initialize answers
    const initialAnswers: QuestionAnswer[] = Array.from({ length: totalQuestions }, (_, i) => ({
      questionNumber: i + 1,
      omrDetected: null,
      aiVerified: null,
      manualEntry: null,
      omrConfidence: 0,
      aiConfidence: 0,
      omrAiMatch: null,
      aiManualMatch: null,
      finalAnswer: null,
      status: 'pending',
    }));

    // Simulate OMR detection with progress
    for (let i = 0; i < totalQuestions; i++) {
      await new Promise(r => setTimeout(r, 50));
      const detected = options[Math.floor(Math.random() * 4)];
      const confidence = 0.85 + Math.random() * 0.14;
      
      initialAnswers[i] = {
        ...initialAnswers[i],
        omrDetected: detected,
        omrConfidence: confidence,
      };
      
      setAnswers([...initialAnswers]);
    }

    toast.success('OMR Detection Complete!', { id: 'omr' });
    setIsLoading(false);
  };

  // Phase 2: AI Verification
  const runAIVerification = async () => {
    if (answers.filter(a => a.omrDetected).length === 0) {
      toast.error('Run OMR Detection first');
      return;
    }

    setIsLoading(true);
    setCurrentPhase('ai');
    toast.loading('Running AI Verification...', { id: 'ai' });

    const updatedAnswers = [...answers];

    for (let i = 0; i < answers.length; i++) {
      await new Promise(r => setTimeout(r, 80));
      
      // AI might agree or disagree with OMR
      const aiAgrees = Math.random() > 0.15; // 85% agreement rate
      const aiAnswer = aiAgrees ? updatedAnswers[i].omrDetected : options[Math.floor(Math.random() * 4)];
      const aiConfidence = 0.80 + Math.random() * 0.18;
      const omrAiMatch = aiAnswer === updatedAnswers[i].omrDetected;

      updatedAnswers[i] = {
        ...updatedAnswers[i],
        aiVerified: aiAnswer,
        aiConfidence,
        omrAiMatch,
        status: omrAiMatch ? 'pending' : 'review',
      };

      setAnswers([...updatedAnswers]);
    }

    toast.success('AI Verification Complete!', { id: 'ai' });
    setIsLoading(false);
  };

  // Phase 3: Manual Entry
  const handleManualEntry = (questionNumber: number, answer: string) => {
    setAnswers(prev => prev.map(a => {
      if (a.questionNumber === questionNumber) {
        const aiManualMatch = answer === a.aiVerified;
        const allMatch = a.omrDetected === a.aiVerified && a.aiVerified === answer;
        
        return {
          ...a,
          manualEntry: answer,
          aiManualMatch,
          finalAnswer: allMatch ? answer : null,
          status: allMatch ? 'matched' : (aiManualMatch ? 'pending' : 'mismatch'),
        };
      }
      return a;
    }));
  };

  // Bulk manual entry (copy from AI)
  const copyAIToManual = () => {
    setAnswers(prev => prev.map(a => ({
      ...a,
      manualEntry: a.aiVerified,
      aiManualMatch: true,
      finalAnswer: a.omrAiMatch ? a.aiVerified : null,
      status: a.omrAiMatch ? 'matched' : 'mismatch',
    })));
    toast.success('Copied AI answers to manual entry');
  };

  // Finalize verification
  const finalizeVerification = () => {
    const mismatches = answers.filter(a => a.status === 'mismatch' || a.status === 'review');
    
    if (mismatches.length > 0) {
      toast.error(`${mismatches.length} questions need review before finalizing`);
      setShowOnlyMismatches(true);
      return;
    }

    setCurrentPhase('complete');
    setAnswers(prev => prev.map(a => ({
      ...a,
      finalAnswer: a.manualEntry || a.aiVerified || a.omrDetected,
      status: 'matched',
    })));
    
    toast.success('Verification complete! Results locked on blockchain.');
  };

  // Override a specific answer
  const overrideAnswer = (questionNumber: number, answer: string, source: 'omr' | 'ai' | 'manual') => {
    setAnswers(prev => prev.map(a => {
      if (a.questionNumber === questionNumber) {
        return {
          ...a,
          finalAnswer: answer,
          status: 'matched',
          notes: `Overridden with ${source.toUpperCase()} answer`,
        };
      }
      return a;
    }));
    toast.success(`Q${questionNumber} finalized with ${source.toUpperCase()} answer: ${answer}`);
  };

  const getMatchIcon = (match: boolean | null) => {
    if (match === null) return <Minus className="w-4 h-4 text-muted-foreground" />;
    return match ? 
      <Check className="w-4 h-4 text-green-500" /> : 
      <X className="w-4 h-4 text-red-500" />;
  };

  const getStatusBadge = (status: QuestionAnswer['status']) => {
    switch (status) {
      case 'matched':
        return <Badge className="bg-green-500 text-white">MATCHED</Badge>;
      case 'mismatch':
        return <Badge className="bg-red-500 text-white">MISMATCH</Badge>;
      case 'review':
        return <Badge className="bg-yellow-500 text-white">REVIEW</Badge>;
      default:
        return <Badge variant="secondary">PENDING</Badge>;
    }
  };

  const filteredAnswers = showOnlyMismatches 
    ? answers.filter(a => a.status === 'mismatch' || a.status === 'review')
    : answers;

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b-4 border-foreground bg-card">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Link to="/admin/dashboard">
            <Button variant="outline" size="sm" className="mb-4 border-2 border-foreground">
              <ArrowLeft className="w-4 h-4 mr-2" />
              BACK TO DASHBOARD
            </Button>
          </Link>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold">ANSWER VERIFICATION</h1>
              <p className="text-sm font-mono text-muted-foreground mt-2">
                3-Way Answer Tally: OMR Detection → AI Verification → Manual Entry
              </p>
            </div>
            <Badge variant="outline" className="border-2 border-chart-1 px-4 py-2">
              <Shield className="w-4 h-4 mr-2" />
              TRIPLE VERIFICATION
            </Badge>
          </div>
        </div>
      </header>

      <section className="py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">

          {/* Verification Pipeline */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <Card className="p-6 border-4 border-foreground shadow-lg">
              <h3 className="text-xl font-bold mb-6">VERIFICATION PIPELINE</h3>
              
              <div className="flex items-center justify-between gap-4">
                {/* Step 1: OMR */}
                <div className={`flex-1 p-4 border-4 rounded-lg transition-all ${
                  currentPhase === 'omr' ? 'border-blue-500 bg-blue-50 dark:bg-blue-950/20' :
                  stats.omrDetected > 0 ? 'border-green-500 bg-green-50 dark:bg-green-950/20' :
                  'border-muted'
                }`}>
                  <div className="flex items-center gap-3 mb-3">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      stats.omrDetected > 0 ? 'bg-green-500' : 
                      currentPhase === 'omr' ? 'bg-blue-500 animate-pulse' : 'bg-muted'
                    } text-white`}>
                      {stats.omrDetected > 0 ? <CheckCircle2 className="w-5 h-5" /> : 
                       currentPhase === 'omr' ? <Loader2 className="w-5 h-5 animate-spin" /> :
                       <ScanLine className="w-5 h-5" />}
                    </div>
                    <div>
                      <h4 className="font-bold">OMR DETECTION</h4>
                      <p className="text-xs text-muted-foreground">Scan student answers</p>
                    </div>
                  </div>
                  <div className="text-2xl font-black mb-2">{stats.omrDetected}/{totalQuestions}</div>
                  <Button 
                    size="sm" 
                    className="w-full"
                    onClick={runOMRDetection}
                    disabled={isLoading}
                  >
                    {currentPhase === 'omr' ? 'DETECTING...' : 'RUN OMR'}
                  </Button>
                </div>

                <ChevronRight className="w-6 h-6 text-muted-foreground flex-shrink-0" />

                {/* Step 2: AI */}
                <div className={`flex-1 p-4 border-4 rounded-lg transition-all ${
                  currentPhase === 'ai' ? 'border-blue-500 bg-blue-50 dark:bg-blue-950/20' :
                  stats.aiVerified > 0 ? 'border-green-500 bg-green-50 dark:bg-green-950/20' :
                  'border-muted'
                }`}>
                  <div className="flex items-center gap-3 mb-3">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      stats.aiVerified > 0 ? 'bg-green-500' : 
                      currentPhase === 'ai' ? 'bg-blue-500 animate-pulse' : 'bg-muted'
                    } text-white`}>
                      {stats.aiVerified > 0 ? <CheckCircle2 className="w-5 h-5" /> : 
                       currentPhase === 'ai' ? <Loader2 className="w-5 h-5 animate-spin" /> :
                       <Brain className="w-5 h-5" />}
                    </div>
                    <div>
                      <h4 className="font-bold">AI VERIFICATION</h4>
                      <p className="text-xs text-muted-foreground">AI solves & compares</p>
                    </div>
                  </div>
                  <div className="text-2xl font-black mb-2">{stats.aiVerified}/{totalQuestions}</div>
                  <Button 
                    size="sm" 
                    className="w-full"
                    onClick={runAIVerification}
                    disabled={isLoading || stats.omrDetected === 0}
                  >
                    {currentPhase === 'ai' ? 'VERIFYING...' : 'RUN AI'}
                  </Button>
                </div>

                <ChevronRight className="w-6 h-6 text-muted-foreground flex-shrink-0" />

                {/* Step 3: Manual */}
                <div className={`flex-1 p-4 border-4 rounded-lg transition-all ${
                  currentPhase === 'manual' ? 'border-blue-500 bg-blue-50 dark:bg-blue-950/20' :
                  stats.manualEntered === totalQuestions ? 'border-green-500 bg-green-50 dark:bg-green-950/20' :
                  'border-muted'
                }`}>
                  <div className="flex items-center gap-3 mb-3">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      stats.manualEntered === totalQuestions ? 'bg-green-500' : 
                      currentPhase === 'manual' ? 'bg-blue-500' : 'bg-muted'
                    } text-white`}>
                      {stats.manualEntered === totalQuestions ? <CheckCircle2 className="w-5 h-5" /> : 
                       <UserCheck className="w-5 h-5" />}
                    </div>
                    <div>
                      <h4 className="font-bold">MANUAL ENTRY</h4>
                      <p className="text-xs text-muted-foreground">Human verification</p>
                    </div>
                  </div>
                  <div className="text-2xl font-black mb-2">{stats.manualEntered}/{totalQuestions}</div>
                  <p className="text-xs text-muted-foreground text-center">Enter answers below</p>
                </div>

                <ChevronRight className="w-6 h-6 text-muted-foreground flex-shrink-0" />

                {/* Final */}
                <div className={`flex-1 p-4 border-4 rounded-lg transition-all ${
                  currentPhase === 'complete' ? 'border-green-500 bg-green-50 dark:bg-green-950/20' :
                  'border-muted'
                }`}>
                  <div className="flex items-center gap-3 mb-3">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      currentPhase === 'complete' ? 'bg-green-500' : 'bg-muted'
                    } text-white`}>
                      {currentPhase === 'complete' ? <Lock className="w-5 h-5" /> : 
                       <Shield className="w-5 h-5" />}
                    </div>
                    <div>
                      <h4 className="font-bold">FINALIZE</h4>
                      <p className="text-xs text-muted-foreground">Lock on blockchain</p>
                    </div>
                  </div>
                  <div className="text-2xl font-black mb-2">{stats.allMatched}/{totalQuestions}</div>
                  <Button 
                    size="sm" 
                    className="w-full bg-green-600 hover:bg-green-700"
                    onClick={finalizeVerification}
                    disabled={stats.manualEntered < totalQuestions}
                  >
                    FINALIZE
                  </Button>
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Stats Overview */}
          {answers.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="grid grid-cols-2 md:grid-cols-4 gap-4"
            >
              <Card className="p-4 border-4 border-green-500">
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-8 h-8 text-green-500" />
                  <div>
                    <p className="text-2xl font-black">{stats.allMatched}</p>
                    <p className="text-xs font-mono text-muted-foreground">ALL MATCHED</p>
                  </div>
                </div>
              </Card>
              <Card className="p-4 border-4 border-red-500">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="w-8 h-8 text-red-500" />
                  <div>
                    <p className="text-2xl font-black">{stats.mismatches}</p>
                    <p className="text-xs font-mono text-muted-foreground">MISMATCHES</p>
                  </div>
                </div>
              </Card>
              <Card className="p-4 border-4 border-yellow-500">
                <div className="flex items-center gap-3">
                  <Eye className="w-8 h-8 text-yellow-500" />
                  <div>
                    <p className="text-2xl font-black">{stats.pendingReview}</p>
                    <p className="text-xs font-mono text-muted-foreground">NEED REVIEW</p>
                  </div>
                </div>
              </Card>
              <Card className="p-4 border-4 border-chart-2">
                <div className="flex items-center gap-3">
                  <Calculator className="w-8 h-8 text-chart-2" />
                  <div>
                    <p className="text-2xl font-black">
                      {stats.allMatched > 0 ? ((stats.allMatched / totalQuestions) * 100).toFixed(0) : 0}%
                    </p>
                    <p className="text-xs font-mono text-muted-foreground">MATCH RATE</p>
                  </div>
                </div>
              </Card>
            </motion.div>
          )}

          {/* Answer Comparison Table */}
          {answers.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <Card className="border-4 border-foreground shadow-lg overflow-hidden">
                <div className="p-4 border-b-2 border-foreground bg-muted/50 flex items-center justify-between">
                  <h3 className="text-xl font-bold">ANSWER COMPARISON</h3>
                  <div className="flex items-center gap-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowOnlyMismatches(!showOnlyMismatches)}
                      className="border-2"
                    >
                      {showOnlyMismatches ? <Eye className="w-4 h-4 mr-2" /> : <EyeOff className="w-4 h-4 mr-2" />}
                      {showOnlyMismatches ? 'SHOW ALL' : 'SHOW MISMATCHES'}
                    </Button>
                    <Button variant="outline" size="sm" className="border-2">
                      <Download className="w-4 h-4 mr-2" />
                      EXPORT
                    </Button>
                  </div>
                </div>

                {/* Table Header */}
                <div className="grid grid-cols-12 gap-2 p-3 bg-muted/30 border-b-2 border-foreground text-xs font-bold">
                  <div className="col-span-1">Q#</div>
                  <div className="col-span-2 text-center">OMR DETECTED</div>
                  <div className="col-span-1 text-center">≟</div>
                  <div className="col-span-2 text-center">AI VERIFIED</div>
                  <div className="col-span-1 text-center">≟</div>
                  <div className="col-span-2 text-center">MANUAL ENTRY</div>
                  <div className="col-span-2 text-center">STATUS</div>
                  <div className="col-span-1 text-center">ACTION</div>
                </div>

                {/* Table Body */}
                <div className="max-h-[500px] overflow-y-auto">
                  {filteredAnswers.map((answer) => (
                    <div key={answer.questionNumber}>
                      <div 
                        className={`grid grid-cols-12 gap-2 p-3 border-b items-center transition-colors ${
                          answer.status === 'mismatch' ? 'bg-red-50 dark:bg-red-950/10' :
                          answer.status === 'review' ? 'bg-yellow-50 dark:bg-yellow-950/10' :
                          answer.status === 'matched' ? 'bg-green-50 dark:bg-green-950/10' : ''
                        }`}
                      >
                        <div className="col-span-1 font-bold">Q{answer.questionNumber}</div>
                        
                        {/* OMR Detected */}
                        <div className="col-span-2 text-center">
                          {answer.omrDetected ? (
                            <div className="flex items-center justify-center gap-2">
                              <span className="font-black text-lg">{answer.omrDetected}</span>
                              <span className="text-xs text-muted-foreground">
                                ({(answer.omrConfidence * 100).toFixed(0)}%)
                              </span>
                            </div>
                          ) : (
                            <span className="text-muted-foreground">—</span>
                          )}
                        </div>

                        {/* OMR vs AI Match */}
                        <div className="col-span-1 flex justify-center">
                          {getMatchIcon(answer.omrAiMatch)}
                        </div>

                        {/* AI Verified */}
                        <div className="col-span-2 text-center">
                          {answer.aiVerified ? (
                            <div className="flex items-center justify-center gap-2">
                              <span className="font-black text-lg">{answer.aiVerified}</span>
                              <span className="text-xs text-muted-foreground">
                                ({(answer.aiConfidence * 100).toFixed(0)}%)
                              </span>
                            </div>
                          ) : (
                            <span className="text-muted-foreground">—</span>
                          )}
                        </div>

                        {/* AI vs Manual Match */}
                        <div className="col-span-1 flex justify-center">
                          {getMatchIcon(answer.aiManualMatch)}
                        </div>

                        {/* Manual Entry */}
                        <div className="col-span-2 flex justify-center gap-1">
                          {options.map((opt) => (
                            <button
                              key={opt}
                              onClick={() => handleManualEntry(answer.questionNumber, opt)}
                              className={`w-8 h-8 border-2 font-bold text-sm transition-all ${
                                answer.manualEntry === opt 
                                  ? 'border-chart-2 bg-chart-2 text-white' 
                                  : 'border-foreground hover:bg-muted'
                              }`}
                            >
                              {opt}
                            </button>
                          ))}
                        </div>

                        {/* Status */}
                        <div className="col-span-2 flex justify-center">
                          {getStatusBadge(answer.status)}
                        </div>

                        {/* Action */}
                        <div className="col-span-1 flex justify-center">
                          {(answer.status === 'mismatch' || answer.status === 'review') && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => setExpandedQuestion(
                                expandedQuestion === answer.questionNumber ? null : answer.questionNumber
                              )}
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                          )}
                        </div>
                      </div>

                      {/* Expanded Review Panel */}
                      <AnimatePresence>
                        {expandedQuestion === answer.questionNumber && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="bg-muted/30 border-b-2 border-foreground overflow-hidden"
                          >
                            <div className="p-4">
                              <h4 className="font-bold mb-3 flex items-center gap-2">
                                <AlertTriangle className="w-4 h-4 text-yellow-500" />
                                RESOLVE MISMATCH - Q{answer.questionNumber}
                              </h4>
                              <div className="grid grid-cols-3 gap-4">
                                <div 
                                  className="p-4 border-2 border-foreground cursor-pointer hover:bg-muted transition-colors"
                                  onClick={() => overrideAnswer(answer.questionNumber, answer.omrDetected!, 'omr')}
                                >
                                  <div className="flex items-center gap-2 mb-2">
                                    <ScanLine className="w-4 h-4" />
                                    <span className="font-bold text-sm">USE OMR</span>
                                  </div>
                                  <p className="text-3xl font-black text-center">{answer.omrDetected}</p>
                                  <p className="text-xs text-center text-muted-foreground mt-1">
                                    Confidence: {(answer.omrConfidence * 100).toFixed(0)}%
                                  </p>
                                </div>
                                <div 
                                  className="p-4 border-2 border-foreground cursor-pointer hover:bg-muted transition-colors"
                                  onClick={() => overrideAnswer(answer.questionNumber, answer.aiVerified!, 'ai')}
                                >
                                  <div className="flex items-center gap-2 mb-2">
                                    <Brain className="w-4 h-4" />
                                    <span className="font-bold text-sm">USE AI</span>
                                  </div>
                                  <p className="text-3xl font-black text-center">{answer.aiVerified}</p>
                                  <p className="text-xs text-center text-muted-foreground mt-1">
                                    Confidence: {(answer.aiConfidence * 100).toFixed(0)}%
                                  </p>
                                </div>
                                <div 
                                  className="p-4 border-2 border-foreground cursor-pointer hover:bg-muted transition-colors"
                                  onClick={() => overrideAnswer(answer.questionNumber, answer.manualEntry!, 'manual')}
                                >
                                  <div className="flex items-center gap-2 mb-2">
                                    <UserCheck className="w-4 h-4" />
                                    <span className="font-bold text-sm">USE MANUAL</span>
                                  </div>
                                  <p className="text-3xl font-black text-center">{answer.manualEntry || '—'}</p>
                                  <p className="text-xs text-center text-muted-foreground mt-1">
                                    Human verified
                                  </p>
                                </div>
                              </div>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  ))}
                </div>
              </Card>
            </motion.div>
          )}

          {/* Empty State */}
          {answers.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <Card className="p-12 border-4 border-dashed border-muted text-center">
                <div className="flex flex-col items-center gap-4">
                  <div className="w-20 h-20 border-4 border-foreground bg-muted flex items-center justify-center">
                    <ScanLine className="w-10 h-10" />
                  </div>
                  <h3 className="text-2xl font-bold">START VERIFICATION</h3>
                  <p className="text-muted-foreground font-mono max-w-md">
                    Click "RUN OMR" to begin the 3-way answer verification process.
                    OMR detection will scan answers, AI will verify, and you'll confirm manually.
                  </p>
                  <Button onClick={runOMRDetection} className="mt-4">
                    <Sparkles className="w-4 h-4 mr-2" />
                    START OMR DETECTION
                  </Button>
                </div>
              </Card>
            </motion.div>
          )}

          {/* How It Works */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card className="p-6 border-4 border-chart-4 shadow-lg">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Sparkles className="w-5 h-5" />
                3-WAY VERIFICATION PROCESS
              </h3>
              <div className="grid md:grid-cols-3 gap-6">
                <div className="border-2 border-muted p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <ScanLine className="w-5 h-5 text-chart-2" />
                    <h4 className="font-bold">1. OMR DETECTION</h4>
                  </div>
                  <p className="text-sm font-mono text-muted-foreground">
                    AI scans the OMR sheet and detects student's marked answers with confidence scores
                  </p>
                </div>
                <div className="border-2 border-muted p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Brain className="w-5 h-5 text-chart-4" />
                    <h4 className="font-bold">2. AI VERIFICATION</h4>
                  </div>
                  <p className="text-sm font-mono text-muted-foreground">
                    AI independently solves questions and compares with OMR detected answers
                  </p>
                </div>
                <div className="border-2 border-muted p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <UserCheck className="w-5 h-5 text-green-500" />
                    <h4 className="font-bold">3. MANUAL ENTRY</h4>
                  </div>
                  <p className="text-sm font-mono text-muted-foreground">
                    Human verifier enters answers to compare with AI. Mismatches are flagged for review
                  </p>
                </div>
              </div>
            </Card>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default AnswerVerification;
