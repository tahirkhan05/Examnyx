import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Landing from "./pages/Landing";
import StudentLogin from "./pages/auth/StudentLogin";
import AdminLogin from "./pages/auth/AdminLogin";
import StudentDashboard from "./pages/student/StudentDashboard";
import Results from "./pages/student/Results";
import OMRVerification from "./pages/student/OMRVerification";
import Challenges from "./pages/student/Challenges";
import Blockchain from "./pages/student/Blockchain";
import AdminDashboard from "./pages/admin/AdminDashboard";
import BatchCreation from "./pages/admin/BatchCreation";
import AnomalyReview from "./pages/admin/AnomalyReview";
import Analytics from "./pages/admin/Analytics";
import BlockchainAudit from "./pages/admin/BlockchainAudit";
import AdminOMRVerification from "./pages/admin/OMRVerification";
import AnswerVerification from "./pages/admin/AnswerVerification";
import ProtectedRoute from "./components/ProtectedRoute";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<Landing />} />
          <Route path="/student/login" element={<StudentLogin />} />
          <Route path="/admin/login" element={<AdminLogin />} />

          {/* Student Routes */}
          <Route
            path="/student/dashboard"
            element={
              <ProtectedRoute allowedRoles={["student"]}>
                <StudentDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/student/results"
            element={
              <ProtectedRoute allowedRoles={["student"]}>
                <Results />
              </ProtectedRoute>
            }
          />
          <Route
            path="/student/omr-verification"
            element={
              <ProtectedRoute allowedRoles={["student"]}>
                <OMRVerification />
              </ProtectedRoute>
            }
          />
          <Route
            path="/student/challenges"
            element={
              <ProtectedRoute allowedRoles={["student"]}>
                <Challenges />
              </ProtectedRoute>
            }
          />
          <Route
            path="/student/blockchain"
            element={
              <ProtectedRoute allowedRoles={["student"]}>
                <Blockchain />
              </ProtectedRoute>
            }
          />

          {/* Admin Routes */}
          <Route
            path="/admin/dashboard"
            element={
              <ProtectedRoute allowedRoles={["institution_admin", "exam_center_operator"]}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/batch-creation"
            element={
              <ProtectedRoute allowedRoles={["institution_admin", "exam_center_operator"]}>
                <BatchCreation />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/anomaly-review"
            element={
              <ProtectedRoute allowedRoles={["institution_admin", "exam_center_operator"]}>
                <AnomalyReview />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/analytics"
            element={
              <ProtectedRoute allowedRoles={["institution_admin", "exam_center_operator"]}>
                <Analytics />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/blockchain"
            element={
              <ProtectedRoute allowedRoles={["institution_admin", "exam_center_operator"]}>
                <BlockchainAudit />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/omr-verification"
            element={
              <ProtectedRoute allowedRoles={["institution_admin", "exam_center_operator"]}>
                <AdminOMRVerification />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/answer-verification"
            element={
              <ProtectedRoute allowedRoles={["institution_admin", "exam_center_operator"]}>
                <AnswerVerification />
              </ProtectedRoute>
            }
          />

          {/* 404 */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
