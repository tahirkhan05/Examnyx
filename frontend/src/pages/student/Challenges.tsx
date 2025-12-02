import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ArrowLeft, AlertCircle, Plus, Loader2, Brain, Lock, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { toast } from 'sonner';
import { apiService } from '@/services/api.service';

interface AIResponse {
  student_valid: boolean;
  reason: string;
  alternative_valid: boolean;
  question_ambiguous: boolean;
  key_incorrect: boolean;
  flag_for_human_review: boolean;
  final_recommendation: string;
  confidence: number;
  ai_solution?: string;
  ai_explanation?: string;
}

interface Challenge {
  id: string;
  examName: string;
  questionNumber: number;
  questionText: string;
  yourAnswer: string;
  officialAnswer: string;
  reason: string;
  status: 'pending' | 'approved' | 'rejected' | 'under_review';
  submittedDate: string;
  aiResponse?: AIResponse;
}

const Challenges = () => {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isResponseDialogOpen, setIsResponseDialogOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [selectedChallenge, setSelectedChallenge] = useState<Challenge | null>(null);
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [newChallenge, setNewChallenge] = useState({
    examName: '',
    questionNumber: '',
    questionText: '',
    yourAnswer: '',
    officialAnswer: '',
    reason: '',
    subject: '',
  });

  // Update time every second for realtime display
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Load mock challenges with AI responses
  useEffect(() => {
    const mockChallenges: Challenge[] = [
      {
        id: '1',
        examName: 'Computer Science Mid-Term',
        questionNumber: 15,
        questionText: 'Which sorting algorithm has the best average-case time complexity?',
        yourAnswer: 'B',
        officialAnswer: 'A',
        reason: 'Quick Sort has O(n log n) average case, same as Merge Sort',
        status: 'under_review',
        submittedDate: '2024-11-25T10:30:00',
        aiResponse: {
          student_valid: true,
          reason: 'The student is correct that Quick Sort has O(n log n) average-case time complexity, which is the same as Merge Sort (option A). Both answers could be considered correct depending on the exact question wording.',
          alternative_valid: true,
          question_ambiguous: true,
          key_incorrect: false,
          flag_for_human_review: true,
          final_recommendation: 'Accept both answers as valid due to question ambiguity',
          confidence: 0.87,
          ai_solution: 'Both Merge Sort and Quick Sort have O(n log n) average-case complexity',
          ai_explanation: 'Quick Sort: O(n log n) average, O(n²) worst. Merge Sort: O(n log n) all cases. Both are optimal comparison-based sorts.'
        }
      },
      {
        id: '2',
        examName: 'Mathematics Quiz',
        questionNumber: 8,
        questionText: 'What is the derivative of sin(x)?',
        yourAnswer: 'C',
        officialAnswer: 'D',
        reason: 'cos(x) is the correct derivative of sin(x)',
        status: 'approved',
        submittedDate: '2024-11-18T14:45:00',
        aiResponse: {
          student_valid: true,
          reason: 'The student correctly identifies that the derivative of sin(x) is cos(x). If option C represents cos(x), the official key marking D as correct appears to be an error.',
          alternative_valid: false,
          question_ambiguous: false,
          key_incorrect: true,
          flag_for_human_review: false,
          final_recommendation: 'Update answer key to accept cos(x) as correct answer',
          confidence: 0.98,
          ai_solution: 'cos(x)',
          ai_explanation: 'Using standard calculus: d/dx[sin(x)] = cos(x). This is a fundamental derivative rule.'
        }
      },
      {
        id: '3',
        examName: 'Physics Lab Test',
        questionNumber: 22,
        questionText: 'What is the SI unit of force?',
        yourAnswer: 'A',
        officialAnswer: 'B',
        reason: 'I believe Newton is the correct SI unit',
        status: 'rejected',
        submittedDate: '2024-11-12T09:15:00',
        aiResponse: {
          student_valid: false,
          reason: 'If option A is Joule and option B is Newton, then the official key is correct. Newton (N) is the SI unit of force, while Joule (J) is the SI unit of energy. The student may have confused force with work/energy.',
          alternative_valid: false,
          question_ambiguous: false,
          key_incorrect: false,
          flag_for_human_review: false,
          final_recommendation: 'Maintain original marking - official key is correct',
          confidence: 0.99,
          ai_solution: 'Newton (N)',
          ai_explanation: 'Force = mass × acceleration. SI unit: kg·m/s² = Newton (N). Named after Sir Isaac Newton.'
        }
      },
    ];
    setChallenges(mockChallenges);
  }, []);

  const handleSubmitChallenge = async () => {
    if (!newChallenge.examName || !newChallenge.questionNumber || !newChallenge.yourAnswer || !newChallenge.officialAnswer || !newChallenge.reason || !newChallenge.questionText) {
      toast.error('Please fill in all fields including the question text');
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      // Call AI evaluation service
      const aiResponse = await apiService.submitChallenge({
        questionText: newChallenge.questionText,
        studentAnswer: newChallenge.yourAnswer,
        studentProof: newChallenge.reason,
        officialKey: newChallenge.officialAnswer,
        subject: newChallenge.subject || newChallenge.examName,
        examId: newChallenge.examName,
        questionNumber: parseInt(newChallenge.questionNumber)
      });
      
      // Create new challenge with AI response
      const newChallengeEntry: Challenge = {
        id: Date.now().toString(),
        examName: newChallenge.examName,
        questionNumber: parseInt(newChallenge.questionNumber),
        questionText: newChallenge.questionText,
        yourAnswer: newChallenge.yourAnswer,
        officialAnswer: newChallenge.officialAnswer,
        reason: newChallenge.reason,
        status: aiResponse.flag_for_human_review ? 'under_review' : (aiResponse.student_valid ? 'approved' : 'rejected'),
        submittedDate: new Date().toISOString(),
        aiResponse: aiResponse
      };
      
      setChallenges(prev => [newChallengeEntry, ...prev]);
      setSelectedChallenge(newChallengeEntry);
      setIsDialogOpen(false);
      setIsResponseDialogOpen(true);
      
      toast.success('Challenge submitted and evaluated by AI!');
      
      setNewChallenge({
        examName: '',
        questionNumber: '',
        questionText: '',
        yourAnswer: '',
        officialAnswer: '',
        reason: '',
        subject: '',
      });
    } catch (error: any) {
      console.error('Challenge submission error:', error);
      
      // Fallback: Create challenge without AI response (will be reviewed manually)
      const newChallengeEntry: Challenge = {
        id: Date.now().toString(),
        examName: newChallenge.examName,
        questionNumber: parseInt(newChallenge.questionNumber),
        questionText: newChallenge.questionText,
        yourAnswer: newChallenge.yourAnswer,
        officialAnswer: newChallenge.officialAnswer,
        reason: newChallenge.reason,
        status: 'pending',
        submittedDate: new Date().toISOString(),
      };
      
      setChallenges(prev => [newChallengeEntry, ...prev]);
      setIsDialogOpen(false);
      
      toast.warning('Challenge submitted for manual review. AI evaluation is temporarily unavailable.');
      
      setNewChallenge({
        examName: '',
        questionNumber: '',
        questionText: '',
        yourAnswer: '',
        officialAnswer: '',
        reason: '',
        subject: '',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const viewChallengeDetails = (challenge: Challenge) => {
    setSelectedChallenge(challenge);
    setIsResponseDialogOpen(true);
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    });
  };

  const getTimeDifference = (timestamp: string) => {
    const now = currentTime.getTime();
    const then = new Date(timestamp).getTime();
    const diff = now - then;
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  };

  const getStatusBadge = (status: string) => {
    const variants = {
      pending: { variant: 'secondary' as const, text: '⏳ PENDING', icon: Loader2 },
      approved: { variant: 'default' as const, text: '✓ APPROVED', icon: CheckCircle },
      rejected: { variant: 'outline' as const, text: '✗ REJECTED', icon: XCircle },
      under_review: { variant: 'secondary' as const, text: '🔍 UNDER REVIEW', icon: AlertTriangle },
    };
    const config = variants[status as keyof typeof variants] || variants.pending;
    return <Badge variant={config.variant} className="border-2 border-foreground">{config.text}</Badge>;
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600';
    if (confidence >= 0.7) return 'text-yellow-600';
    return 'text-red-600';
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
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold">CHALLENGE & DISPUTE</h1>
              <p className="text-sm font-mono text-muted-foreground mt-2">
                Raise objections and track dispute status
              </p>
            </div>
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
              <DialogTrigger asChild>
                <Button className="border-2 border-foreground shadow-md">
                  <Plus className="w-4 h-4 mr-2" />
                  NEW CHALLENGE
                </Button>
              </DialogTrigger>
              <DialogContent className="border-4 border-foreground max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle className="text-2xl font-bold">SUBMIT NEW CHALLENGE</DialogTitle>
                  <DialogDescription className="font-mono text-muted-foreground">
                    Provide the question details and your reasoning. AI will analyze your challenge against the locked answer key.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="exam" className="font-bold">EXAM NAME</Label>
                      <Input
                        id="exam"
                        placeholder="e.g., Computer Science Mid-Term"
                        value={newChallenge.examName}
                        onChange={(e) => setNewChallenge({ ...newChallenge, examName: e.target.value })}
                        className="border-2 border-foreground"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="subject" className="font-bold">SUBJECT</Label>
                      <Select 
                        value={newChallenge.subject}
                        onValueChange={(value) => setNewChallenge({ ...newChallenge, subject: value })}
                      >
                        <SelectTrigger className="border-2 border-foreground">
                          <SelectValue placeholder="Select Subject" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Mathematics">Mathematics</SelectItem>
                          <SelectItem value="Physics">Physics</SelectItem>
                          <SelectItem value="Chemistry">Chemistry</SelectItem>
                          <SelectItem value="Computer Science">Computer Science</SelectItem>
                          <SelectItem value="Biology">Biology</SelectItem>
                          <SelectItem value="English">English</SelectItem>
                          <SelectItem value="General">General</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="questionText" className="font-bold">QUESTION TEXT <span className="text-red-500">*</span></Label>
                    <Textarea
                      id="questionText"
                      placeholder="Enter the full question text from the exam paper..."
                      value={newChallenge.questionText}
                      onChange={(e) => setNewChallenge({ ...newChallenge, questionText: e.target.value })}
                      className="border-2 border-foreground min-h-[80px]"
                    />
                    <p className="text-xs text-muted-foreground">AI will analyze this question to provide reasoning</p>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="question" className="font-bold">QUESTION NO.</Label>
                      <Input
                        id="question"
                        type="number"
                        placeholder="15"
                        value={newChallenge.questionNumber}
                        onChange={(e) => setNewChallenge({ ...newChallenge, questionNumber: e.target.value })}
                        className="border-2 border-foreground"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="yourAnswer" className="font-bold">YOUR ANSWER</Label>
                      <Select 
                        value={newChallenge.yourAnswer}
                        onValueChange={(value) => setNewChallenge({ ...newChallenge, yourAnswer: value })}
                      >
                        <SelectTrigger className="border-2 border-foreground">
                          <SelectValue placeholder="Select" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="A">A</SelectItem>
                          <SelectItem value="B">B</SelectItem>
                          <SelectItem value="C">C</SelectItem>
                          <SelectItem value="D">D</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="official" className="font-bold flex items-center gap-1">
                        <Lock className="w-3 h-3" />
                        OFFICIAL ANSWER
                      </Label>
                      <Select 
                        value={newChallenge.officialAnswer}
                        onValueChange={(value) => setNewChallenge({ ...newChallenge, officialAnswer: value })}
                      >
                        <SelectTrigger className="border-2 border-foreground">
                          <SelectValue placeholder="Select" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="A">A</SelectItem>
                          <SelectItem value="B">B</SelectItem>
                          <SelectItem value="C">C</SelectItem>
                          <SelectItem value="D">D</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="reason" className="font-bold">REASON FOR CHALLENGE <span className="text-red-500">*</span></Label>
                    <Textarea
                      id="reason"
                      placeholder="Explain why you believe the official answer is incorrect. Include any supporting references, formulas, or evidence..."
                      value={newChallenge.reason}
                      onChange={(e) => setNewChallenge({ ...newChallenge, reason: e.target.value })}
                      className="border-2 border-foreground min-h-[120px]"
                    />
                  </div>
                  <Card className="p-3 border-2 border-chart-3 bg-chart-3/10">
                    <div className="flex items-start gap-2">
                      <Brain className="w-5 h-5 mt-0.5 text-chart-3" />
                      <div className="text-sm">
                        <p className="font-bold text-chart-3">AI-POWERED EVALUATION</p>
                        <p className="text-muted-foreground">Your challenge will be analyzed by AI against the locked answer key from the blockchain. You'll receive instant reasoning and recommendation.</p>
                      </div>
                    </div>
                  </Card>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsDialogOpen(false)} className="border-2 border-foreground" disabled={isSubmitting}>
                    CANCEL
                  </Button>
                  <Button onClick={handleSubmitChallenge} className="border-2 border-foreground shadow-md" disabled={isSubmitting}>
                    {isSubmitting ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        ANALYZING...
                      </>
                    ) : (
                      <>
                        <Brain className="w-4 h-4 mr-2" />
                        SUBMIT & EVALUATE
                      </>
                    )}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </header>

      <section className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Info Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <Card className="p-6 border-4 border-chart-3 shadow-lg mb-8">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 border-2 border-foreground bg-background flex items-center justify-center flex-shrink-0">
                  <AlertCircle className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-xl font-bold mb-2">HOW TO RAISE A CHALLENGE</h3>
                  <p className="text-sm font-mono text-muted-foreground leading-relaxed">
                    Submit your objection with supporting proof. Our evaluation team will review your case within 48 hours. 
                    All challenges are verified by both AI and human reviewers for fairness.
                  </p>
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Challenges Table */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="border-4 border-foreground shadow-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="border-b-2 border-foreground">
                    <TableHead className="font-bold font-mono">EXAM</TableHead>
                    <TableHead className="font-bold font-mono">QUESTION</TableHead>
                    <TableHead className="font-bold font-mono">YOUR ANSWER</TableHead>
                    <TableHead className="font-bold font-mono">
                      <div className="flex items-center gap-1">
                        <Lock className="w-3 h-3" />
                        OFFICIAL
                      </div>
                    </TableHead>
                    <TableHead className="font-bold font-mono">STATUS</TableHead>
                    <TableHead className="font-bold font-mono">SUBMITTED</TableHead>
                    <TableHead className="font-bold font-mono">AI VERDICT</TableHead>
                    <TableHead className="font-bold font-mono">ACTIONS</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {challenges.map((challenge) => (
                    <TableRow key={challenge.id} className="border-b-2 border-muted hover:bg-muted/50 cursor-pointer" onClick={() => viewChallengeDetails(challenge)}>
                      <TableCell className="font-mono">{challenge.examName}</TableCell>
                      <TableCell className="font-bold">Q{challenge.questionNumber}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="border-2 border-foreground">
                          {challenge.yourAnswer}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="border-2 border-foreground">
                          {challenge.officialAnswer}
                        </Badge>
                      </TableCell>
                      <TableCell>{getStatusBadge(challenge.status)}</TableCell>
                      <TableCell className="font-mono text-xs">{formatTimestamp(challenge.submittedDate)}</TableCell>
                      <TableCell>
                        {challenge.aiResponse ? (
                          <div className="flex items-center gap-1">
                            {challenge.aiResponse.student_valid ? (
                              <CheckCircle className="w-4 h-4 text-green-600" />
                            ) : (
                              <XCircle className="w-4 h-4 text-red-600" />
                            )}
                            <span className={`text-xs font-mono ${getConfidenceColor(challenge.aiResponse.confidence)}`}>
                              {Math.round(challenge.aiResponse.confidence * 100)}%
                            </span>
                          </div>
                        ) : (
                          <span className="text-xs text-muted-foreground">Pending</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Button variant="ghost" size="sm" className="border border-foreground" onClick={(e) => { e.stopPropagation(); viewChallengeDetails(challenge); }}>
                          VIEW
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          </motion.div>

          {/* AI Response Dialog */}
          <Dialog open={isResponseDialogOpen} onOpenChange={setIsResponseDialogOpen}>
            <DialogContent className="border-4 border-foreground max-w-3xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle className="text-2xl font-bold flex items-center gap-2">
                  <Brain className="w-6 h-6" />
                  AI EVALUATION RESPONSE
                </DialogTitle>
                <DialogDescription className="font-mono text-muted-foreground">
                  Analysis from the locked answer key with AI reasoning
                </DialogDescription>
              </DialogHeader>
              
              {selectedChallenge && (
                <div className="space-y-4 py-4">
                  {/* Question Info */}
                  <Card className="p-4 border-2 border-foreground">
                    <div className="grid grid-cols-2 gap-4 mb-3">
                      <div>
                        <span className="text-xs font-mono text-muted-foreground">EXAM</span>
                        <p className="font-bold">{selectedChallenge.examName}</p>
                      </div>
                      <div>
                        <span className="text-xs font-mono text-muted-foreground">QUESTION</span>
                        <p className="font-bold">Q{selectedChallenge.questionNumber}</p>
                      </div>
                    </div>
                    {selectedChallenge.questionText && (
                      <div className="mt-3 p-3 bg-muted rounded-lg">
                        <span className="text-xs font-mono text-muted-foreground">QUESTION TEXT</span>
                        <p className="mt-1">{selectedChallenge.questionText}</p>
                      </div>
                    )}
                  </Card>

                  {/* Answer Comparison */}
                  <div className="grid grid-cols-2 gap-4">
                    <Card className="p-4 border-2 border-blue-500">
                      <span className="text-xs font-mono text-muted-foreground">YOUR ANSWER</span>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="outline" className="text-lg px-3 py-1 border-2">{selectedChallenge.yourAnswer}</Badge>
                      </div>
                      <p className="text-sm mt-2 text-muted-foreground">{selectedChallenge.reason}</p>
                    </Card>
                    <Card className="p-4 border-2 border-orange-500">
                      <span className="text-xs font-mono text-muted-foreground flex items-center gap-1">
                        <Lock className="w-3 h-3" />
                        LOCKED OFFICIAL ANSWER
                      </span>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="secondary" className="text-lg px-3 py-1 border-2">{selectedChallenge.officialAnswer}</Badge>
                      </div>
                      <p className="text-xs mt-2 text-muted-foreground">From blockchain-secured answer key</p>
                    </Card>
                  </div>

                  {selectedChallenge.aiResponse ? (
                    <>
                      {/* AI Solution */}
                      <Card className="p-4 border-2 border-chart-3">
                        <div className="flex items-center gap-2 mb-3">
                          <Brain className="w-5 h-5 text-chart-3" />
                          <span className="font-bold text-chart-3">AI's ANALYSIS</span>
                          <Badge variant="outline" className={`ml-auto ${getConfidenceColor(selectedChallenge.aiResponse.confidence)}`}>
                            {Math.round(selectedChallenge.aiResponse.confidence * 100)}% CONFIDENCE
                          </Badge>
                        </div>
                        
                        {selectedChallenge.aiResponse.ai_solution && (
                          <div className="mb-3 p-3 bg-chart-3/10 rounded-lg">
                            <span className="text-xs font-mono text-muted-foreground">AI's CALCULATED ANSWER</span>
                            <p className="font-bold mt-1">{selectedChallenge.aiResponse.ai_solution}</p>
                          </div>
                        )}
                        
                        {selectedChallenge.aiResponse.ai_explanation && (
                          <div className="mb-3 p-3 bg-muted rounded-lg">
                            <span className="text-xs font-mono text-muted-foreground">STEP-BY-STEP REASONING</span>
                            <p className="mt-1 text-sm">{selectedChallenge.aiResponse.ai_explanation}</p>
                          </div>
                        )}
                      </Card>

                      {/* Verdict */}
                      <Card className={`p-4 border-2 ${selectedChallenge.aiResponse.student_valid ? 'border-green-500 bg-green-50 dark:bg-green-950/20' : 'border-red-500 bg-red-50 dark:bg-red-950/20'}`}>
                        <div className="flex items-center gap-2 mb-2">
                          {selectedChallenge.aiResponse.student_valid ? (
                            <CheckCircle className="w-5 h-5 text-green-600" />
                          ) : (
                            <XCircle className="w-5 h-5 text-red-600" />
                          )}
                          <span className={`font-bold ${selectedChallenge.aiResponse.student_valid ? 'text-green-700 dark:text-green-400' : 'text-red-700 dark:text-red-400'}`}>
                            {selectedChallenge.aiResponse.student_valid ? 'YOUR CHALLENGE IS VALID' : 'CHALLENGE NOT SUPPORTED'}
                          </span>
                        </div>
                        <p className="text-sm">{selectedChallenge.aiResponse.reason}</p>
                      </Card>

                      {/* Additional Flags */}
                      <div className="grid grid-cols-2 gap-3">
                        {selectedChallenge.aiResponse.alternative_valid && (
                          <div className="flex items-center gap-2 p-2 bg-yellow-50 dark:bg-yellow-950/20 rounded-lg border border-yellow-500">
                            <AlertTriangle className="w-4 h-4 text-yellow-600" />
                            <span className="text-sm">Alternative answer valid</span>
                          </div>
                        )}
                        {selectedChallenge.aiResponse.question_ambiguous && (
                          <div className="flex items-center gap-2 p-2 bg-orange-50 dark:bg-orange-950/20 rounded-lg border border-orange-500">
                            <AlertCircle className="w-4 h-4 text-orange-600" />
                            <span className="text-sm">Question is ambiguous</span>
                          </div>
                        )}
                        {selectedChallenge.aiResponse.key_incorrect && (
                          <div className="flex items-center gap-2 p-2 bg-red-50 dark:bg-red-950/20 rounded-lg border border-red-500">
                            <XCircle className="w-4 h-4 text-red-600" />
                            <span className="text-sm">Official key may be incorrect</span>
                          </div>
                        )}
                        {selectedChallenge.aiResponse.flag_for_human_review && (
                          <div className="flex items-center gap-2 p-2 bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-500">
                            <AlertCircle className="w-4 h-4 text-blue-600" />
                            <span className="text-sm">Flagged for human review</span>
                          </div>
                        )}
                      </div>

                      {/* Recommendation */}
                      <Card className="p-4 border-2 border-foreground bg-muted/50">
                        <span className="text-xs font-mono text-muted-foreground">FINAL RECOMMENDATION</span>
                        <p className="mt-1 font-medium">{selectedChallenge.aiResponse.final_recommendation}</p>
                      </Card>
                    </>
                  ) : (
                    <Card className="p-6 border-2 border-muted text-center">
                      <Loader2 className="w-8 h-8 mx-auto mb-2 animate-spin text-muted-foreground" />
                      <p className="text-muted-foreground">AI evaluation pending...</p>
                      <p className="text-xs text-muted-foreground mt-1">Your challenge is awaiting AI analysis</p>
                    </Card>
                  )}
                </div>
              )}
              
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsResponseDialogOpen(false)} className="border-2 border-foreground">
                  CLOSE
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </section>
    </div>
  );
};

export default Challenges;
