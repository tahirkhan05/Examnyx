import api from '@/lib/api';

// Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface BlockchainBlock {
  block_index: number;
  block_type: string;
  timestamp: number;
  previous_hash: string;
  hash: string;
  data: any;
  signatures?: any[];
}

export interface StudentResult {
  student_id: string;
  exam_id: string;
  total_marks: number;
  obtained_marks: number;
  percentage: number;
  grade: string;
  blockchain_hash?: string;
  timestamp?: string;
}

export interface OMRSheet {
  sheet_id: string;
  student_id: string;
  exam_id: string;
  scan_url?: string;
  bubble_detections?: any;
  status: string;
  blockchain_hash?: string;
}

// API Service Functions

export const apiService = {
  // Health Check
  async healthCheck() {
    const response = await api.get('/health');
    return response.data;
  },

  // Blockchain APIs
  async getBlockchainStatus() {
    const response = await api.get('/api/blockchain/status');
    return response.data;
  },

  async getBlockchainBlocks(limit?: number) {
    const params = limit ? { limit } : {};
    const response = await api.get('/api/blockchain/blocks', { params });
    return response.data;
  },

  async getBlockByHash(hash: string) {
    const response = await api.get(`/api/blockchain/block/${hash}`);
    return response.data;
  },

  async validateBlockchain() {
    const response = await api.get('/api/blockchain/validate');
    return response.data;
  },

  // OMR Scan APIs
  async uploadOMRSheet(file: File, metadata: any) {
    try {
      // First, try the new format with base64 encoding
      const reader = new FileReader();
      
      return new Promise((resolve, reject) => {
        reader.onload = async () => {
          try {
            const base64Content = reader.result as string;
            const base64Data = base64Content.split(',')[1]; // Remove data:image/jpeg;base64, prefix
            
            // Calculate file hash (simple implementation)
            const fileHash = await this.calculateFileHash(file);
            
            const sheetId = `SHEET_${metadata.student_id}_${Date.now()}`;
            
            const requestData = {
              sheet_id: sheetId,
              roll_number: metadata.student_id || 'UNKNOWN',
              exam_id: metadata.exam_id || 'EXAM_001',
              student_name: metadata.student_name || 'Student',
              file_hash: fileHash,
              file_content: base64Data,
              metadata: metadata
            };
            
            const response = await api.post('/api/scan/create', requestData);
            resolve(response.data);
          } catch (error) {
            // If the new endpoint doesn't work, try multipart upload
            try {
              const formData = new FormData();
              formData.append('file', file);
              formData.append('metadata', JSON.stringify(metadata));

              const uploadResponse = await api.post('/api/scan/upload', formData, {
                headers: {
                  'Content-Type': 'multipart/form-data',
                },
              });
              resolve(uploadResponse.data);
            } catch (uploadError) {
              reject(uploadError);
            }
          }
        };
        
        reader.onerror = () => reject(new Error('Failed to read file'));
        reader.readAsDataURL(file);
      });
    } catch (error) {
      throw error;
    }
  },

  async calculateFileHash(file: File): Promise<string> {
    // Simple hash implementation using file properties
    const content = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', content);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return hashHex;
  },

  async getOMRSheet(sheetId: string) {
    const response = await api.get(`/api/scan/${sheetId}`);
    return response.data;
  },

  // Bubble Detection APIs
  async processBubbleDetection(sheetId: string) {
    const response = await api.post(`/api/bubble/process/${sheetId}`);
    return response.data;
  },

  async getBubbleDetectionResults(sheetId: string) {
    const response = await api.get(`/api/bubble/${sheetId}`);
    return response.data;
  },

  // Scoring APIs
  async scoreOMRSheet(sheetId: string, answerKey: any) {
    const response = await api.post(`/api/score/calculate/${sheetId}`, { answer_key: answerKey });
    return response.data;
  },

  async getScoreResults(sheetId: string) {
    const response = await api.get(`/api/score/${sheetId}`);
    return response.data;
  },

  // Verification APIs
  async submitVerification(sheetId: string, verificationData: any) {
    const response = await api.post(`/api/verify/submit/${sheetId}`, verificationData);
    return response.data;
  },

  async getVerificationStatus(sheetId: string) {
    const response = await api.get(`/api/verify/status/${sheetId}`);
    return response.data;
  },

  // Result APIs
  async finalizeResult(sheetId: string) {
    const response = await api.post(`/api/result/finalize/${sheetId}`);
    return response.data;
  },

  async getStudentResults(studentId: string) {
    const response = await api.get(`/api/result/student/${studentId}`);
    return response.data;
  },

  async getResultByHash(blockchainHash: string) {
    const response = await api.get(`/api/result/hash/${blockchainHash}`);
    return response.data;
  },

  // Recheck APIs
  async submitRecheckRequest(sheetId: string, reason: string, evidence?: any) {
    const response = await api.post(`/api/recheck/request/${sheetId}`, {
      reason,
      evidence,
    });
    return response.data;
  },

  async getRecheckRequests(studentId?: string) {
    const params = studentId ? { student_id: studentId } : {};
    const response = await api.get('/api/recheck/requests', { params });
    return response.data;
  },

  async processRecheck(recheckId: string, decision: 'approve' | 'reject', notes?: string) {
    const response = await api.post(`/api/recheck/process/${recheckId}`, {
      decision,
      notes,
    });
    return response.data;
  },

  // AI Integration APIs
  async getAIConfidence(sheetId: string) {
    const response = await api.get(`/api/ai/confidence/${sheetId}`);
    return response.data;
  },

  async requestAIArbitration(sheetId: string, conflictData: any) {
    const response = await api.post(`/api/ai/arbitrate/${sheetId}`, conflictData);
    return response.data;
  },

  // Question Paper APIs
  async createQuestionPaper(questionPaperData: any) {
    const response = await api.post('/api/question-paper/upload', questionPaperData);
    return response.data;
  },

  async getQuestionPaper(questionPaperId: string) {
    const response = await api.get(`/api/question-paper/${questionPaperId}`);
    return response.data;
  },

  async listQuestionPapers() {
    const response = await api.get('/api/question-paper/list');
    return response.data;
  },

  // Quality Control APIs
  async uploadForQualityCheck(file: File, questionPaperId: string) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('question_paper_id', questionPaperId);

    const response = await api.post('/api/quality/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async getQualityReport(sheetId: string) {
    const response = await api.get(`/api/quality/report/${sheetId}`);
    return response.data;
  },

  // Evaluation APIs
  async startEvaluation(evaluationData: any) {
    const response = await api.post('/api/evaluation/start', evaluationData);
    return response.data;
  },

  async getEvaluationStatus(evaluationId: string) {
    const response = await api.get(`/api/evaluation/status/${evaluationId}`);
    return response.data;
  },

  async listEvaluations(filters?: any) {
    const response = await api.get('/api/evaluation/list', { params: filters });
    return response.data;
  },

  // Intervention APIs
  async getInterventionsRequired() {
    const response = await api.get('/api/interventions/required');
    return response.data;
  },

  async resolveIntervention(interventionId: string, resolution: any) {
    const response = await api.post(`/api/interventions/resolve/${interventionId}`, resolution);
    return response.data;
  },

  // Workflow APIs
  async getWorkflowStatus(workflowId: string) {
    const response = await api.get(`/api/workflow/pipeline/${workflowId}`);
    return response.data;
  },

  async completeWorkflow(requestData: any) {
    const response = await api.post(`/api/workflow/complete`, requestData);
    return response.data;
  },

  // Challenge & Dispute APIs
  async submitChallenge(challengeData: {
    questionText: string;
    studentAnswer: string;
    studentProof: string;
    officialKey: string;
    subject?: string;
    examId?: string;
    questionNumber?: number;
  }) {
    // First, get the AI's solution for the question
    const solveResponse = await api.post('/api/ai/solve', {
      question_text: challengeData.questionText,
      subject: challengeData.subject || 'General',
      difficulty_level: 'medium'
    });
    
    const aiSolution = solveResponse.data?.ai_solution || '';
    
    // Then evaluate the student's objection
    const response = await api.post('/api/ai/student-objection', {
      question_text: challengeData.questionText,
      student_answer: challengeData.studentAnswer,
      student_proof: challengeData.studentProof,
      official_key: challengeData.officialKey,
      ai_solution: aiSolution,
      subject: challengeData.subject
    });
    
    return {
      ...response.data,
      ai_solution: aiSolution,
      ai_explanation: solveResponse.data?.explanation || ''
    };
  },

  async evaluateStudentObjection(objectionData: {
    questionText: string;
    studentAnswer: string;
    studentProof: string;
    officialKey: string;
    aiSolution?: string;
    subject?: string;
  }) {
    const response = await api.post('/api/ai/student-objection', {
      question_text: objectionData.questionText,
      student_answer: objectionData.studentAnswer,
      student_proof: objectionData.studentProof,
      official_key: objectionData.officialKey,
      ai_solution: objectionData.aiSolution,
      subject: objectionData.subject
    });
    return response.data;
  },

  async solveQuestion(questionData: {
    questionText: string;
    subject: string;
    difficultyLevel?: string;
  }) {
    const response = await api.post('/api/ai/solve', {
      question_text: questionData.questionText,
      subject: questionData.subject,
      difficulty_level: questionData.difficultyLevel || 'medium'
    });
    return response.data;
  },

  async verifyAnswer(verificationData: {
    questionText: string;
    aiSolution: string;
    officialKey: string;
    subject?: string;
  }) {
    const response = await api.post('/api/ai/verify', {
      question_text: verificationData.questionText,
      ai_solution: verificationData.aiSolution,
      official_key: verificationData.officialKey,
      subject: verificationData.subject
    });
    return response.data;
  },

  async getAnswerKey(keyId: string) {
    const response = await api.get(`/api/question-paper/answer-key/${keyId}`);
    return response.data;
  },

  async getChallengeStatus() {
    const response = await api.get('/api/ai/flag-status');
    return response.data;
  },

  async getFlaggedItems() {
    const response = await api.get('/api/ai/flagged-items');
    return response.data;
  },

  // OMR Evaluation APIs
  async evaluateOMRSheet(evaluationData: {
    sheet_id: string;
    image_base64: string;
    student_id?: string;
    exam_id?: string;
    num_questions?: number;
    answer_key_id?: string;
  }) {
    const response = await api.post('/api/omr/evaluate', {
      sheet_id: evaluationData.sheet_id,
      image_base64: evaluationData.image_base64,
      student_id: evaluationData.student_id,
      exam_id: evaluationData.exam_id,
      num_questions: evaluationData.num_questions || 50,
      answer_key_id: evaluationData.answer_key_id
    });
    return response.data;
  },

  async quickEvaluateOMR(evaluationData: {
    image_base64: string;
    answer_key: string;
    num_questions?: number;
  }) {
    const response = await api.post('/api/omr/quick-evaluate', {
      image_base64: evaluationData.image_base64,
      answer_key: evaluationData.answer_key,
      num_questions: evaluationData.num_questions || 10
    });
    return response.data;
  },

  async getOMREvaluationStatus(sheetId: string) {
    const response = await api.get(`/api/omr/status/${sheetId}`);
    return response.data;
  },
};

export default apiService;
