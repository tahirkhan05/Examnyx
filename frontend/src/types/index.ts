export type UserRole = 'student' | 'institution_admin' | 'exam_center_operator';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  rollNumber?: string;
  employeeId?: string;
  department?: string;
  phoneNumber?: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string, role: UserRole) => Promise<void>;
  logout: () => void;
}

export interface OMRSheet {
  id: string;
  studentName: string;
  rollNumber: string;
  examName: string;
  uploadDate: string;
  status: 'pending' | 'processing' | 'verified' | 'under_review';
  confidence: number;
  totalMarks?: number;
  obtainedMarks?: number;
}

export interface Anomaly {
  id: string;
  sheetId: string;
  questionNumber: number;
  type: 'low_confidence' | 'multiple_marks' | 'unclear_bubble' | 'damage';
  confidence: number;
  detectedAnswer: string;
  suggestedAnswer?: string;
  status: 'pending' | 'reviewed' | 'override';
}

export interface QuestionAnalytics {
  questionNumber: number;
  correctRate: number;
  anomalyCount: number;
  avgConfidence: number;
  riskLevel: 'low' | 'medium' | 'high';
}

export interface BatchStats {
  totalSheets: number;
  sheetsProcessed: number;
  pendingAnomalies: number;
  avgConfidence: number;
  etaMinutes: number;
  releaseStatus: 'locked' | 'ready';
}
