import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, FileText, Download, TrendingUp, Award, Shield } from 'lucide-react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useToast } from '@/hooks/use-toast';
import apiService from '@/services/api.service';
import { useAuthStore } from '@/store/authStore';

const Results = () => {
  const { user } = useAuthStore();
  const { toast } = useToast();
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [blockchainStatus, setBlockchainStatus] = useState<any>(null);

  useEffect(() => {
    fetchResults();
    fetchBlockchainStatus();
  }, []);

  const fetchResults = async () => {
    try {
      setLoading(true);
      const response = await apiService.getStudentResults(user?.id || user?.rollNumber || 'STUDENT_001');
      if (response.success) {
        setResults(response.data || []);
      } else {
        setResults(getMockResults());
      }
    } catch (error) {
      console.error('Error fetching results:', error);
      toast({
        title: 'Info',
        description: 'Showing sample data. Connect backend to see real results.',
        variant: 'default',
      });
      setResults(getMockResults());
    } finally {
      setLoading(false);
    }
  };

  const fetchBlockchainStatus = async () => {
    try {
      const response = await apiService.getBlockchainStatus();
      if (response.success) {
        setBlockchainStatus(response.data);
      }
    } catch (error) {
      console.error('Error fetching blockchain status:', error);
    }
  };

  const verifyBlockchainHash = async (hash: string) => {
    try {
      const response = await apiService.getBlockByHash(hash);
      if (response.success) {
        toast({
          title: '✓ Blockchain Verified',
          description: `Result verified on block #${response.data.block_index}`,
        });
      }
    } catch (error: any) {
      toast({
        title: 'Verification Error',
        description: error.message || 'Unable to verify blockchain hash',
        variant: 'destructive',
      });
    }
  };

  const getMockResults = () => [
    {
      id: '1',
      student_id: 'STUDENT_001',
      exam_id: 'CSC_MT_001',
      examName: 'Computer Science Mid-Term',
      date: '2024-11-20',
      totalMarks: 100,
      obtainedMarks: 87,
      total_marks: 100,
      obtained_marks: 87,
      percentage: 87,
      grade: 'A',
      status: 'verified' as const,
      blockchain_hash: '0xabc123...',
    },
    {
      id: '2',
      student_id: 'STUDENT_001',
      exam_id: 'MATH_QZ_001',
      examName: 'Mathematics Quiz',
      date: '2024-11-15',
      totalMarks: 50,
      obtainedMarks: 42,
      total_marks: 50,
      obtained_marks: 42,
      percentage: 84,
      grade: 'B+',
      status: 'verified' as const,
      blockchain_hash: '0xdef456...',
    },
    {
      id: '3',
      student_id: 'STUDENT_001',
      exam_id: 'PHY_LT_001',
      examName: 'Physics Lab Test',
      date: '2024-11-10',
      totalMarks: 75,
      obtainedMarks: 68,
      total_marks: 75,
      obtained_marks: 68,
      percentage: 90.67,
      grade: 'A',
      status: 'under_review' as const,
      blockchain_hash: null,
    },
  ];

  const getStatusBadge = (status: string) => {
    const variants = {
      verified: { variant: 'default' as const, text: '✓ VERIFIED' },
      pending: { variant: 'outline' as const, text: '⏳ PENDING' },
      under_review: { variant: 'secondary' as const, text: '🔍 REVIEW' },
    };
    const config = variants[status as keyof typeof variants] || variants.pending;
    return <Badge variant={config.variant} className="border-2 border-foreground">{config.text}</Badge>;
  };

  const avgScore = results.length > 0
    ? results.reduce((acc, r) => acc + ((r.obtained_marks || r.obtainedMarks) / (r.total_marks || r.totalMarks)) * 100, 0) / results.length
    : 0;

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-foreground border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="font-mono text-muted-foreground">Loading results...</p>
        </div>
      </div>
    );
  }

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
              <h1 className="text-4xl font-bold">RESULT SUMMARY</h1>
              <p className="text-sm font-mono text-muted-foreground mt-2">
                View your exam performance and download reports
              </p>
            </div>
            {blockchainStatus && (
              <Badge variant="outline" className="border-2 border-chart-4">
                <Shield className="w-3 h-3 mr-1" />
                Blockchain: {blockchainStatus.total_blocks} Blocks
              </Badge>
            )}
          </div>
        </div>
      </header>

      <section className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              <Card className="p-6 border-4 border-chart-1 shadow-lg">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 border-2 border-foreground bg-background flex items-center justify-center">
                    <FileText className="w-6 h-6" />
                  </div>
                  <div>
                    <div className="text-3xl font-bold">{results.length}</div>
                    <div className="text-sm font-mono text-muted-foreground">TOTAL EXAMS</div>
                  </div>
                </div>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <Card className="p-6 border-4 border-chart-2 shadow-lg">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 border-2 border-foreground bg-background flex items-center justify-center">
                    <TrendingUp className="w-6 h-6" />
                  </div>
                  <div>
                    <div className="text-3xl font-bold">{avgScore.toFixed(1)}%</div>
                    <div className="text-sm font-mono text-muted-foreground">AVERAGE SCORE</div>
                  </div>
                </div>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <Card className="p-6 border-4 border-chart-3 shadow-lg">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 border-2 border-foreground bg-background flex items-center justify-center">
                    <Award className="w-6 h-6" />
                  </div>
                  <div>
                    <div className="text-3xl font-bold">
                      {results.filter(r => r.grade?.startsWith('A')).length}
                    </div>
                    <div className="text-sm font-mono text-muted-foreground">A GRADES</div>
                  </div>
                </div>
              </Card>
            </motion.div>
          </div>

          {/* Results Table */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card className="border-4 border-foreground shadow-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="border-b-2 border-foreground">
                    <TableHead className="font-bold font-mono">EXAM</TableHead>
                    <TableHead className="font-bold font-mono">DATE</TableHead>
                    <TableHead className="font-bold font-mono">SCORE</TableHead>
                    <TableHead className="font-bold font-mono">GRADE</TableHead>
                    <TableHead className="font-bold font-mono">STATUS</TableHead>
                    <TableHead className="font-bold font-mono">ACTIONS</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {results.map((result, index) => (
                    <motion.tr
                      key={result.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.5 + index * 0.1 }}
                      className="border-b border-border hover:bg-muted/30"
                    >
                      <TableCell className="font-mono">
                        {result.examName || result.exam_name || `Exam ${result.exam_id}`}
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {result.date || (result.timestamp ? new Date(result.timestamp).toLocaleDateString() : 'N/A')}
                      </TableCell>
                      <TableCell className="font-bold">
                        {result.obtained_marks || result.obtainedMarks}/{result.total_marks || result.totalMarks}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="border-2 border-foreground">
                          {result.grade}
                        </Badge>
                      </TableCell>
                      <TableCell>{getStatusBadge(result.status)}</TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button size="sm" variant="outline" className="border-2 border-foreground">
                            <FileText className="w-4 h-4 mr-2" />
                            VIEW
                          </Button>
                          <Button size="sm" variant="outline" className="border-2 border-foreground">
                            <Download className="w-4 h-4" />
                          </Button>
                          {result.blockchain_hash && (
                            <Button
                              size="sm"
                              variant="outline"
                              className="border-2 border-chart-4"
                              onClick={() => verifyBlockchainHash(result.blockchain_hash)}
                            >
                              <Shield className="w-4 h-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </motion.tr>
                  ))}
                </TableBody>
              </Table>
            </Card>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default Results;
