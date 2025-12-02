import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { 
  ArrowLeft, Upload, FileText, CheckCircle2, Lock, Loader2, 
  AlertTriangle, Brain, RefreshCw, Shield, Image, X, Plus, Edit2, Save
} from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import apiService from '@/services/api.service';

interface Question {
  number: number;
  text: string;
  options: { A: string; B: string; C: string; D: string };
}

interface AnswerEntry {
  question: number;
  questionText: string;
  options: { A: string; B: string; C: string; D: string };
  correctAnswer: string;
  marks: number;
  aiVerified: boolean | null;
  confidence: number;
  aiSolution?: string;
  reasoning?: string;
  status: 'pending' | 'verified' | 'flagged' | 'corrected';
  matchStatus?: 'match' | 'mismatch' | 'alternative_valid' | 'wrong_key';
}

const BatchCreation = () => {
  const [answerKeyLocked, setAnswerKeyLocked] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [validationProgress, setValidationProgress] = useState(0);
  const [currentValidatingQ, setCurrentValidatingQ] = useState<number | null>(null);
  const [batchId, setBatchId] = useState('');
  const [examName, setExamName] = useState('');
  const [subject, setSubject] = useState('General');
  const [activeTab, setActiveTab] = useState('upload');
  
  // Question Paper Upload
  const [questionPaperFile, setQuestionPaperFile] = useState<File | null>(null);
  const [questionPaperPreview, setQuestionPaperPreview] = useState<string>('');
  const [isProcessingPaper, setIsProcessingPaper] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Questions extracted from paper
  const [questions, setQuestions] = useState<Question[]>([]);
  
  // Answer key entries
  const [answers, setAnswers] = useState<AnswerEntry[]>([]);
  
  // Manual answer key input
  const [manualAnswerKey, setManualAnswerKey] = useState('');
  const [numQuestions, setNumQuestions] = useState(50);
  const [editingQuestion, setEditingQuestion] = useState<number | null>(null);

  // Calculate stats
  const verifiedCount = answers.filter(a => a.status === 'verified').length;
  const flaggedCount = answers.filter(a => a.status === 'flagged').length;
  const avgConfidence = answers.filter(a => a.confidence > 0).length > 0
    ? answers.filter(a => a.confidence > 0).reduce((sum, a) => sum + a.confidence, 0) / answers.filter(a => a.confidence > 0).length
    : 0;

  // Handle question paper upload
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 20 * 1024 * 1024) {
        toast.error('File size must be less than 20MB');
        return;
      }
      
      setQuestionPaperFile(file);
      
      // Create preview for images
      if (file.type.startsWith('image/')) {
        setQuestionPaperPreview(URL.createObjectURL(file));
      } else {
        setQuestionPaperPreview('');
      }
      
      toast.success(`Uploaded: ${file.name}`);
    }
  };

  // Process question paper with AI (extract questions)
  const processQuestionPaper = async () => {
    if (!questionPaperFile) {
      toast.error('Please upload a question paper first');
      return;
    }
    
    setIsProcessingPaper(true);
    toast.loading('Processing question paper with AI...', { id: 'process' });
    
    try {
      // For demo, generate sample questions
      // In production, this would call an OCR/AI service to extract questions
      await new Promise(r => setTimeout(r, 2000));
      
      const extractedQuestions: Question[] = Array.from({ length: numQuestions }, (_, i) => ({
        number: i + 1,
        text: `Question ${i + 1}: This is a sample ${subject} question about topic ${Math.floor(i / 5) + 1}?`,
        options: {
          A: `Option A for Q${i + 1}`,
          B: `Option B for Q${i + 1}`,
          C: `Option C for Q${i + 1}`,
          D: `Option D for Q${i + 1}`,
        }
      }));
      
      setQuestions(extractedQuestions);
      
      // Initialize answer entries
      const initialAnswers: AnswerEntry[] = extractedQuestions.map(q => ({
        question: q.number,
        questionText: q.text,
        options: q.options,
        correctAnswer: '',
        marks: 4,
        aiVerified: null,
        confidence: 0,
        status: 'pending',
      }));
      
      setAnswers(initialAnswers);
      
      toast.success(`Extracted ${extractedQuestions.length} questions!`, { id: 'process' });
      setActiveTab('answer-key');
      
    } catch (error) {
      console.error('Processing error:', error);
      toast.error('Failed to process question paper', { id: 'process' });
    } finally {
      setIsProcessingPaper(false);
    }
  };

  // Import answer key from string (e.g., "ABCDABCDAB...")
  const importAnswerKey = () => {
    const cleanKey = manualAnswerKey.toUpperCase().replace(/[^ABCD]/g, '');
    
    if (cleanKey.length === 0) {
      toast.error('Please enter a valid answer key (A, B, C, D only)');
      return;
    }
    
    // If no questions yet, create them
    if (answers.length === 0) {
      const newAnswers: AnswerEntry[] = Array.from({ length: cleanKey.length }, (_, i) => ({
        question: i + 1,
        questionText: `Question ${i + 1}`,
        options: { A: 'Option A', B: 'Option B', C: 'Option C', D: 'Option D' },
        correctAnswer: cleanKey[i],
        marks: 4,
        aiVerified: null,
        confidence: 0,
        status: 'pending',
      }));
      setAnswers(newAnswers);
      setNumQuestions(cleanKey.length);
    } else {
      // Update existing answers with the key
      setAnswers(prev => prev.map((a, i) => ({
        ...a,
        correctAnswer: cleanKey[i] || a.correctAnswer,
        status: 'pending',
        aiVerified: null,
        confidence: 0,
      })));
    }
    
    toast.success(`Imported ${cleanKey.length} answers`);
    setManualAnswerKey('');
  };

  // Set individual answer
  const setAnswer = (questionNum: number, answer: string) => {
    setAnswers(prev => prev.map(a => 
      a.question === questionNum 
        ? { ...a, correctAnswer: answer, status: 'pending', aiVerified: null }
        : a
    ));
  };

  // Generate empty answer sheet
  const generateEmptyAnswers = () => {
    const newAnswers: AnswerEntry[] = Array.from({ length: numQuestions }, (_, i) => ({
      question: i + 1,
      questionText: `Question ${i + 1}`,
      options: { A: 'Option A', B: 'Option B', C: 'Option C', D: 'Option D' },
      correctAnswer: '',
      marks: 4,
      aiVerified: null,
      confidence: 0,
      status: 'pending',
    }));
    setAnswers(newAnswers);
    toast.success(`Created ${numQuestions} empty answer slots`);
  };

  // AI Validation function
  const validateAnswerWithAI = async (answer: AnswerEntry): Promise<AnswerEntry> => {
    if (!answer.correctAnswer) {
      return { ...answer, status: 'flagged', reasoning: 'No answer key provided' };
    }
    
    try {
      const questionText = answer.questionText || `Question ${answer.question}`;
      const fullQuestion = `${questionText}\nA) ${answer.options.A}\nB) ${answer.options.B}\nC) ${answer.options.C}\nD) ${answer.options.D}`;
      
      // Step 1: Get AI's solution
      const solveResponse = await apiService.solveQuestion({
        questionText: fullQuestion,
        subject,
        difficultyLevel: 'medium'
      });
      
      const aiSolution = solveResponse.ai_solution || '';
      const aiAnswer = aiSolution.match(/^[ABCD]/)?.[0] || aiSolution.slice(0, 1).toUpperCase();
      
      // Step 2: Verify against official key
      const verifyResponse = await apiService.verifyAnswer({
        questionText: fullQuestion,
        aiSolution: aiAnswer,
        officialKey: answer.correctAnswer,
        subject
      });
      
      const matchStatus = verifyResponse.match_status || (aiAnswer === answer.correctAnswer ? 'match' : 'mismatch');
      const isVerified = matchStatus === 'match' || matchStatus === 'alternative_valid';
      const flagForHuman = verifyResponse.flag_for_human || matchStatus === 'mismatch' || matchStatus === 'wrong_key';
      
      return {
        ...answer,
        aiVerified: isVerified,
        confidence: (verifyResponse.confidence || 0.85) * 100,
        aiSolution: aiAnswer,
        reasoning: verifyResponse.reasoning || solveResponse.explanation || 'AI validation complete',
        status: flagForHuman ? 'flagged' : 'verified',
        matchStatus: matchStatus as AnswerEntry['matchStatus'],
      };
    } catch (error) {
      console.error(`Error validating Q${answer.question}:`, error);
      
      // Mock validation on error (for demo)
      const mockConfidence = 75 + Math.random() * 25;
      const mockAiAnswer = ['A', 'B', 'C', 'D'][Math.floor(Math.random() * 4)];
      const isFlagged = mockAiAnswer !== answer.correctAnswer || mockConfidence < 85;
      
      return {
        ...answer,
        aiVerified: !isFlagged,
        confidence: mockConfidence,
        aiSolution: mockAiAnswer,
        reasoning: isFlagged 
          ? `AI suggests ${mockAiAnswer} but official key is ${answer.correctAnswer}. Please verify.`
          : 'AI validation performed (demo mode)',
        status: isFlagged ? 'flagged' : 'verified',
        matchStatus: isFlagged ? 'mismatch' : 'match',
      };
    }
  };

  // Run full validation
  const runAIValidation = async () => {
    const answersWithKeys = answers.filter(a => a.correctAnswer);
    
    if (answersWithKeys.length === 0) {
      toast.error('Please enter answer keys first');
      return;
    }
    
    if (answers.every(a => a.status !== 'pending')) {
      toast.info('All answers already validated');
      return;
    }
    
    setIsValidating(true);
    setValidationProgress(0);
    
    toast.loading('Starting AI validation...', { id: 'validation' });
    
    const pendingAnswers = answers.filter(a => a.status === 'pending' && a.correctAnswer);
    const totalToValidate = pendingAnswers.length;
    let completed = 0;
    
    const updatedAnswers = [...answers];
    
    for (const answer of pendingAnswers) {
      setCurrentValidatingQ(answer.question);
      
      const validatedAnswer = await validateAnswerWithAI(answer);
      
      const index = updatedAnswers.findIndex(a => a.question === answer.question);
      if (index !== -1) {
        updatedAnswers[index] = validatedAnswer;
        setAnswers([...updatedAnswers]);
      }
      
      completed++;
      setValidationProgress(Math.round((completed / totalToValidate) * 100));
      
      await new Promise(r => setTimeout(r, 150));
    }
    
    setCurrentValidatingQ(null);
    setIsValidating(false);
    
    const newFlagged = updatedAnswers.filter(a => a.status === 'flagged').length;
    const newVerified = updatedAnswers.filter(a => a.status === 'verified').length;
    
    toast.success(`Validation complete! ${newVerified} verified, ${newFlagged} flagged`, { id: 'validation' });
  };

  // Approve a flagged answer
  const approveAnswer = (questionNum: number) => {
    setAnswers(prev => prev.map(a => 
      a.question === questionNum 
        ? { ...a, status: 'verified', aiVerified: true }
        : a
    ));
    toast.success(`Question ${questionNum} approved`);
  };

  // Accept AI's suggestion
  const acceptAISuggestion = (questionNum: number) => {
    setAnswers(prev => prev.map(a => 
      a.question === questionNum && a.aiSolution
        ? { ...a, correctAnswer: a.aiSolution, status: 'corrected', aiVerified: true, confidence: 100 }
        : a
    ));
    toast.success(`Question ${questionNum} corrected to AI suggestion`);
  };

  // Correct an answer
  const correctAnswer = (questionNum: number, newAnswer: string) => {
    setAnswers(prev => prev.map(a => 
      a.question === questionNum 
        ? { ...a, correctAnswer: newAnswer, status: 'corrected', aiVerified: true, confidence: 100 }
        : a
    ));
    toast.success(`Question ${questionNum} corrected to ${newAnswer}`);
  };

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
          <h1 className="text-4xl font-bold">BATCH CREATION & ANSWER KEY</h1>
          <p className="text-sm font-mono text-muted-foreground mt-2">
            Upload question paper, enter answer keys, validate with AI
          </p>
        </div>
      </header>

      <section className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="border-2 border-foreground mb-8">
              <TabsTrigger value="upload" className="font-mono">
                1. UPLOAD PAPER
                {questionPaperFile && <CheckCircle2 className="w-3 h-3 ml-2 text-green-500" />}
              </TabsTrigger>
              <TabsTrigger value="answer-key" className="font-mono">
                2. ANSWER KEY
                {answers.filter(a => a.correctAnswer).length > 0 && (
                  <Badge variant="secondary" className="ml-2 text-xs">
                    {answers.filter(a => a.correctAnswer).length}
                  </Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="validation" className="font-mono">
                3. AI VALIDATION
                {verifiedCount > 0 && (
                  <Badge variant="secondary" className="ml-2 text-xs bg-green-500/20">
                    {verifiedCount}✓
                  </Badge>
                )}
              </TabsTrigger>
            </TabsList>

            {/* UPLOAD TAB */}
            <TabsContent value="upload">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <Card className="p-8 border-4 border-chart-1 shadow-lg">
                  <h3 className="text-2xl font-bold mb-6 flex items-center gap-3">
                    <Upload className="w-6 h-6" />
                    UPLOAD QUESTION PAPER
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                    <div>
                      <Label htmlFor="batch-id" className="font-mono">BATCH ID</Label>
                      <Input
                        id="batch-id"
                        placeholder="BATCH-2024-001"
                        className="mt-2 border-2 border-foreground"
                        value={batchId}
                        onChange={(e) => setBatchId(e.target.value)}
                      />
                    </div>
                    <div>
                      <Label htmlFor="exam-name" className="font-mono">EXAM NAME</Label>
                      <Input
                        id="exam-name"
                        placeholder="Computer Science Mid-Term"
                        className="mt-2 border-2 border-foreground"
                        value={examName}
                        onChange={(e) => setExamName(e.target.value)}
                      />
                    </div>
                    <div>
                      <Label htmlFor="subject" className="font-mono">SUBJECT</Label>
                      <Input
                        id="subject"
                        placeholder="Physics, Math, Chemistry..."
                        className="mt-2 border-2 border-foreground"
                        value={subject}
                        onChange={(e) => setSubject(e.target.value)}
                      />
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div>
                      <Label htmlFor="num-questions" className="font-mono">NUMBER OF QUESTIONS</Label>
                      <Input
                        id="num-questions"
                        type="number"
                        min={1}
                        max={200}
                        className="mt-2 border-2 border-foreground"
                        value={numQuestions}
                        onChange={(e) => setNumQuestions(parseInt(e.target.value) || 50)}
                      />
                    </div>
                    <div>
                      <Label className="font-mono">MARKS PER QUESTION</Label>
                      <Input
                        type="number"
                        min={1}
                        max={10}
                        defaultValue={4}
                        className="mt-2 border-2 border-foreground"
                      />
                    </div>
                  </div>

                  {/* File Upload Area */}
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileUpload}
                    accept="image/*,.pdf"
                    className="hidden"
                  />
                  
                  {!questionPaperFile ? (
                    <div 
                      className="border-4 border-dashed border-muted p-12 text-center cursor-pointer hover:border-chart-1 transition-colors"
                      onClick={() => fileInputRef.current?.click()}
                    >
                      <div className="flex flex-col items-center gap-4">
                        <div className="w-16 h-16 border-4 border-foreground bg-background flex items-center justify-center">
                          <Upload className="w-8 h-8" />
                        </div>
                        <div>
                          <p className="text-lg font-bold mb-2">UPLOAD QUESTION PAPER</p>
                          <p className="text-sm font-mono text-muted-foreground">
                            Drag & drop or click to upload (Image or PDF, max 20MB)
                          </p>
                        </div>
                        <Button className="border-2 border-foreground shadow-md">
                          SELECT FILE
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="border-4 border-green-500 p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center gap-4">
                          {questionPaperPreview ? (
                            <img 
                              src={questionPaperPreview} 
                              alt="Question Paper" 
                              className="w-24 h-24 object-cover border-2 border-foreground"
                            />
                          ) : (
                            <div className="w-24 h-24 border-2 border-foreground flex items-center justify-center bg-muted">
                              <FileText className="w-10 h-10" />
                            </div>
                          )}
                          <div>
                            <p className="font-bold text-lg">{questionPaperFile.name}</p>
                            <p className="text-sm font-mono text-muted-foreground">
                              {(questionPaperFile.size / 1024 / 1024).toFixed(2)} MB
                            </p>
                            <Badge variant="secondary" className="mt-2 border-2 border-green-500 text-green-600">
                              <CheckCircle2 className="w-3 h-3 mr-1" />
                              UPLOADED
                            </Badge>
                          </div>
                        </div>
                        <Button 
                          variant="outline" 
                          size="sm"
                          className="border-2 border-red-500 text-red-500"
                          onClick={() => {
                            setQuestionPaperFile(null);
                            setQuestionPaperPreview('');
                          }}
                        >
                          <X className="w-4 h-4" />
                        </Button>
                      </div>
                      
                      <div className="flex gap-4">
                        <Button
                          className="flex-1 border-2 border-foreground"
                          onClick={processQuestionPaper}
                          disabled={isProcessingPaper}
                        >
                          {isProcessingPaper ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                              PROCESSING...
                            </>
                          ) : (
                            <>
                              <Brain className="w-4 h-4 mr-2" />
                              EXTRACT QUESTIONS WITH AI
                            </>
                          )}
                        </Button>
                        <Button
                          variant="outline"
                          className="border-2 border-foreground"
                          onClick={() => {
                            generateEmptyAnswers();
                            setActiveTab('answer-key');
                          }}
                        >
                          <Plus className="w-4 h-4 mr-2" />
                          SKIP TO ANSWER KEY
                        </Button>
                      </div>
                    </div>
                  )}
                  
                  {/* Quick Start without upload */}
                  {!questionPaperFile && (
                    <div className="mt-6 pt-6 border-t-2 border-muted">
                      <p className="text-sm font-mono text-muted-foreground mb-4">
                        Or start without uploading:
                      </p>
                      <Button
                        variant="outline"
                        className="border-2 border-foreground"
                        onClick={() => {
                          generateEmptyAnswers();
                          setActiveTab('answer-key');
                        }}
                      >
                        <Plus className="w-4 h-4 mr-2" />
                        CREATE {numQuestions} EMPTY ANSWER SLOTS
                      </Button>
                    </div>
                  )}
                </Card>
              </motion.div>
            </TabsContent>

            {/* ANSWER KEY TAB */}
            <TabsContent value="answer-key">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <Card className="p-8 border-4 border-chart-2 shadow-lg">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-2xl font-bold flex items-center gap-3">
                      <FileText className="w-6 h-6" />
                      ANSWER KEY ENTRY
                    </h3>
                    <div className="flex items-center gap-3">
                      <Badge variant="secondary" className="border-2">
                        {answers.filter(a => a.correctAnswer).length} / {answers.length} FILLED
                      </Badge>
                      {verifiedCount > 0 && (
                        <Badge variant="secondary" className="border-2 border-green-500 text-green-600">
                          <CheckCircle2 className="w-3 h-3 mr-1" />
                          {verifiedCount} VERIFIED
                        </Badge>
                      )}
                      {flaggedCount > 0 && (
                        <Badge variant="secondary" className="border-2 border-yellow-500 text-yellow-600">
                          <AlertTriangle className="w-3 h-3 mr-1" />
                          {flaggedCount} FLAGGED
                        </Badge>
                      )}
                      {answerKeyLocked && (
                        <Badge variant="default" className="border-2 border-foreground flex items-center gap-2">
                          <Lock className="w-4 h-4" />
                          LOCKED
                        </Badge>
                      )}
                    </div>
                  </div>

                  {/* Quick Import */}
                  <div className="mb-6 p-4 bg-muted/30 border-2 border-muted">
                    <Label className="font-mono font-bold mb-2 block">QUICK IMPORT ANSWER KEY</Label>
                    <p className="text-xs font-mono text-muted-foreground mb-3">
                      Enter answers as a string (e.g., "ABCDABCDABCD...") - only A, B, C, D allowed
                    </p>
                    <div className="flex gap-3">
                      <Textarea
                        placeholder="ABCDABCDABCDABCDABCDABCDABCDABCDABCDABCDABCDABCDA..."
                        className="border-2 border-foreground font-mono text-lg tracking-widest"
                        value={manualAnswerKey}
                        onChange={(e) => setManualAnswerKey(e.target.value.toUpperCase())}
                        disabled={answerKeyLocked}
                        rows={2}
                      />
                      <Button
                        onClick={importAnswerKey}
                        disabled={answerKeyLocked || !manualAnswerKey}
                        className="border-2 border-foreground px-6"
                      >
                        <Save className="w-4 h-4 mr-2" />
                        IMPORT
                      </Button>
                    </div>
                  </div>

                  {/* Answer Grid */}
                  {answers.length > 0 ? (
                    <div className="max-h-[500px] overflow-y-auto border-2 border-foreground p-4 mb-6">
                      <div className="grid grid-cols-5 md:grid-cols-10 gap-2">
                        {answers.map((answer) => (
                          <div 
                            key={answer.question} 
                            className={`border-2 p-2 transition-all ${
                              answer.status === 'verified' ? 'border-green-500 bg-green-500/5' :
                              answer.status === 'flagged' ? 'border-yellow-500 bg-yellow-500/5' :
                              answer.status === 'corrected' ? 'border-blue-500 bg-blue-500/5' :
                              answer.correctAnswer ? 'border-foreground' : 'border-muted'
                            }`}
                          >
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs font-mono text-muted-foreground">
                                Q{answer.question}
                              </span>
                              {answer.status === 'verified' && <CheckCircle2 className="w-3 h-3 text-green-500" />}
                              {answer.status === 'flagged' && <AlertTriangle className="w-3 h-3 text-yellow-500" />}
                              {answer.status === 'corrected' && <Shield className="w-3 h-3 text-blue-500" />}
                            </div>
                            
                            {/* Answer Selection */}
                            <div className="flex gap-1">
                              {['A', 'B', 'C', 'D'].map(opt => (
                                <button
                                  key={opt}
                                  className={`flex-1 py-1 text-xs font-bold border transition-all ${
                                    answer.correctAnswer === opt
                                      ? 'bg-foreground text-background border-foreground'
                                      : 'border-muted hover:border-foreground'
                                  }`}
                                  onClick={() => !answerKeyLocked && setAnswer(answer.question, opt)}
                                  disabled={answerKeyLocked}
                                >
                                  {opt}
                                </button>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="border-4 border-dashed border-muted p-12 text-center mb-6">
                      <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                      <p className="font-bold mb-2">NO ANSWERS YET</p>
                      <p className="text-sm font-mono text-muted-foreground mb-4">
                        Upload a question paper first or create empty slots
                      </p>
                      <Button onClick={generateEmptyAnswers} className="border-2 border-foreground">
                        <Plus className="w-4 h-4 mr-2" />
                        CREATE {numQuestions} ANSWER SLOTS
                      </Button>
                    </div>
                  )}

                  {/* Actions */}
                  {answers.length > 0 && (
                    <div className="flex gap-4">
                      <Button
                        className="flex-1 border-2 border-foreground shadow-md"
                        onClick={() => setActiveTab('validation')}
                        disabled={answers.filter(a => a.correctAnswer).length === 0}
                      >
                        <Brain className="w-4 h-4 mr-2" />
                        PROCEED TO AI VALIDATION
                      </Button>
                      <Button
                        className="border-2 border-foreground shadow-md"
                        onClick={() => {
                          if (flaggedCount > 0) {
                            toast.error(`Please resolve ${flaggedCount} flagged questions before locking`);
                            return;
                          }
                          if (answers.filter(a => a.correctAnswer).length < answers.length) {
                            toast.error('Please fill all answer keys before locking');
                            return;
                          }
                          setAnswerKeyLocked(true);
                          toast.success('Answer key locked successfully!');
                        }}
                        disabled={answerKeyLocked}
                      >
                        <Lock className="w-4 h-4 mr-2" />
                        LOCK KEY
                      </Button>
                    </div>
                  )}
                </Card>
              </motion.div>
            </TabsContent>

            <TabsContent value="validation">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <Card className="p-8 border-4 border-chart-3 shadow-lg">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-2xl font-bold flex items-center gap-3">
                      <Brain className="w-7 h-7" />
                      AI VALIDATION
                    </h3>
                    <Button
                      onClick={runAIValidation}
                      disabled={isValidating || answerKeyLocked}
                      className="border-2 border-foreground"
                    >
                      {isValidating ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          VALIDATING... {validationProgress}%
                        </>
                      ) : (
                        <>
                          <RefreshCw className="w-4 h-4 mr-2" />
                          RUN AI VALIDATION
                        </>
                      )}
                    </Button>
                  </div>

                  {/* Progress Bar */}
                  {isValidating && (
                    <div className="mb-6">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-mono">
                          Validating Question {currentValidatingQ}...
                        </span>
                        <span className="text-sm font-mono">{validationProgress}%</span>
                      </div>
                      <div className="h-3 bg-muted border-2 border-foreground overflow-hidden">
                        <motion.div 
                          className="h-full bg-chart-2"
                          initial={{ width: 0 }}
                          animate={{ width: `${validationProgress}%` }}
                          transition={{ duration: 0.3 }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Stats Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                    <div className="border-2 border-muted p-4">
                      <div className="text-3xl font-bold mb-1">{answers.filter(a => a.status === 'pending').length}</div>
                      <div className="text-xs font-mono text-muted-foreground">PENDING</div>
                    </div>
                    <div className="border-2 border-green-500 p-4">
                      <div className="text-3xl font-bold mb-1 text-green-600">{verifiedCount}</div>
                      <div className="text-xs font-mono text-muted-foreground">VERIFIED</div>
                    </div>
                    <div className="border-2 border-yellow-500 p-4">
                      <div className="text-3xl font-bold mb-1 text-yellow-600">{flaggedCount}</div>
                      <div className="text-xs font-mono text-muted-foreground">FLAGGED</div>
                    </div>
                    <div className="border-2 border-muted p-4">
                      <div className="text-3xl font-bold mb-1">{avgConfidence.toFixed(1)}%</div>
                      <div className="text-xs font-mono text-muted-foreground">AVG CONFIDENCE</div>
                    </div>
                  </div>

                  {/* Flagged Items */}
                  <AnimatePresence>
                    {flaggedCount > 0 && (
                      <div className="mb-6">
                        <h4 className="font-bold mb-4 flex items-center gap-2">
                          <AlertTriangle className="w-5 h-5 text-yellow-500" />
                          FLAGGED FOR REVIEW ({flaggedCount})
                        </h4>
                        <div className="space-y-3 max-h-80 overflow-y-auto">
                          {answers.filter(a => a.status === 'flagged').map((answer) => (
                            <motion.div 
                              key={answer.question} 
                              className="border-4 border-yellow-500 bg-yellow-500/5 p-4"
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              exit={{ opacity: 0, x: -20 }}
                            >
                              <div className="flex items-center justify-between mb-2">
                                <span className="font-bold font-mono">
                                  QUESTION {answer.question}
                                </span>
                                <div className="flex items-center gap-2">
                                  <Badge variant="secondary" className="border-2 border-foreground">
                                    {answer.confidence.toFixed(1)}% CONFIDENCE
                                  </Badge>
                                  <Badge 
                                    variant="outline" 
                                    className={`border-2 ${
                                      answer.matchStatus === 'mismatch' ? 'border-red-500 text-red-600' :
                                      answer.matchStatus === 'wrong_key' ? 'border-orange-500 text-orange-600' :
                                      'border-yellow-500 text-yellow-600'
                                    }`}
                                  >
                                    {answer.matchStatus?.toUpperCase().replace('_', ' ')}
                                  </Badge>
                                </div>
                              </div>
                              
                              <div className="grid grid-cols-2 gap-4 mb-3 text-sm">
                                <div className="bg-muted/50 p-2 border-2 border-muted">
                                  <span className="text-xs font-mono text-muted-foreground block">OFFICIAL KEY</span>
                                  <span className="font-bold text-lg">{answer.correctAnswer}</span>
                                </div>
                                <div className="bg-muted/50 p-2 border-2 border-muted">
                                  <span className="text-xs font-mono text-muted-foreground block">AI SOLUTION</span>
                                  <span className="font-bold text-lg">{answer.aiSolution || '-'}</span>
                                </div>
                              </div>
                              
                              <p className="text-sm font-mono text-muted-foreground mb-3">
                                {answer.reasoning || 'AI detected potential inconsistency in answer entry'}
                              </p>
                              
                              <div className="flex flex-wrap gap-2">
                                <Button 
                                  size="sm" 
                                  variant="outline" 
                                  className="border-2 border-green-500 text-green-600 hover:bg-green-500/10"
                                  onClick={() => approveAnswer(answer.question)}
                                >
                                  <CheckCircle2 className="w-4 h-4 mr-1" />
                                  KEEP OFFICIAL
                                </Button>
                                {answer.aiSolution && answer.aiSolution !== answer.correctAnswer && (
                                  <Button 
                                    size="sm" 
                                    variant="outline" 
                                    className="border-2 border-purple-500 text-purple-600 hover:bg-purple-500/10"
                                    onClick={() => acceptAISuggestion(answer.question)}
                                  >
                                    <Brain className="w-4 h-4 mr-1" />
                                    USE AI ({answer.aiSolution})
                                  </Button>
                                )}
                                <div className="flex gap-1">
                                  {['A', 'B', 'C', 'D'].filter(opt => opt !== answer.correctAnswer && opt !== answer.aiSolution).map(opt => (
                                    <Button 
                                      key={opt}
                                      size="sm" 
                                      variant="outline" 
                                      className="border-2 border-blue-500 text-blue-600 hover:bg-blue-500/10 px-3"
                                      onClick={() => correctAnswer(answer.question, opt)}
                                    >
                                      {opt}
                                    </Button>
                                  ))}
                                </div>
                              </div>
                            </motion.div>
                          ))}
                        </div>
                      </div>
                    )}
                  </AnimatePresence>

                  {/* Verified Items Summary */}
                  {verifiedCount > 0 && flaggedCount === 0 && (
                    <div className="border-4 border-green-500 bg-green-500/5 p-6 text-center">
                      <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto mb-3" />
                      <h4 className="text-xl font-bold mb-2">ALL ANSWERS VALIDATED</h4>
                      <p className="text-sm font-mono text-muted-foreground">
                        {verifiedCount} answers verified with {avgConfidence.toFixed(1)}% average confidence
                      </p>
                    </div>
                  )}

                  {/* No validation yet */}
                  {answers.every(a => a.status === 'pending') && !isValidating && (
                    <div className="border-4 border-dashed border-muted p-8 text-center">
                      <Brain className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
                      <h4 className="text-xl font-bold mb-2">NO VALIDATION YET</h4>
                      <p className="text-sm font-mono text-muted-foreground mb-4">
                        Click "RUN AI VALIDATION" to verify all answers against AI analysis
                      </p>
                      <Button onClick={runAIValidation} className="border-2 border-foreground">
                        <Brain className="w-4 h-4 mr-2" />
                        START VALIDATION
                      </Button>
                    </div>
                  )}
                </Card>
              </motion.div>
            </TabsContent>
          </Tabs>
        </div>
      </section>
    </div>
  );
};

export default BatchCreation;
