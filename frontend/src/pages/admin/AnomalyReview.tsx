import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, AlertTriangle, CheckCircle2, XCircle, Eye } from 'lucide-react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const AnomalyReview = () => {
  const mockAnomalies = [
    {
      id: '1',
      sheetId: 'OMR-2024-1001',
      studentName: 'John Doe',
      rollNumber: 'CS2024001',
      questionNumber: 15,
      type: 'low_confidence' as const,
      confidence: 62.5,
      detectedAnswer: 'B',
      suggestedAnswer: 'A',
      status: 'pending' as const,
    },
    {
      id: '2',
      sheetId: 'OMR-2024-1002',
      studentName: 'Jane Smith',
      rollNumber: 'CS2024002',
      questionNumber: 23,
      type: 'multiple_marks' as const,
      confidence: 45.2,
      detectedAnswer: 'C/D',
      suggestedAnswer: 'C',
      status: 'pending' as const,
    },
    {
      id: '3',
      sheetId: 'OMR-2024-1003',
      studentName: 'Mike Johnson',
      rollNumber: 'CS2024003',
      questionNumber: 8,
      type: 'unclear_bubble' as const,
      confidence: 71.3,
      detectedAnswer: 'A',
      suggestedAnswer: 'A',
      status: 'reviewed' as const,
    },
  ];

  const getTypeBadge = (type: string) => {
    const variants = {
      low_confidence: { color: 'border-chart-3', text: '⚠ LOW CONFIDENCE' },
      multiple_marks: { color: 'border-destructive', text: '✗ MULTIPLE MARKS' },
      unclear_bubble: { color: 'border-chart-4', text: '? UNCLEAR' },
      damage: { color: 'border-chart-5', text: '⚡ DAMAGE' },
    };
    const config = variants[type as keyof typeof variants];
    return (
      <Badge variant="outline" className={`border-2 ${config.color}`}>
        {config.text}
      </Badge>
    );
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
          <h1 className="text-4xl font-bold">ANOMALY REVIEW & VERIFICATION</h1>
          <p className="text-sm font-mono text-muted-foreground mt-2">
            Review flagged sheets with AI confidence scores and human override
          </p>
        </div>
      </header>

      <section className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <Card className="p-6 border-4 border-chart-2 shadow-lg">
              <div className="text-3xl font-bold mb-1">47</div>
              <div className="text-xs font-mono text-muted-foreground">TOTAL ANOMALIES</div>
            </Card>
            <Card className="p-6 border-4 border-chart-3 shadow-lg">
              <div className="text-3xl font-bold mb-1">32</div>
              <div className="text-xs font-mono text-muted-foreground">PENDING REVIEW</div>
            </Card>
            <Card className="p-6 border-4 border-chart-1 shadow-lg">
              <div className="text-3xl font-bold mb-1">12</div>
              <div className="text-xs font-mono text-muted-foreground">APPROVED</div>
            </Card>
            <Card className="p-6 border-4 border-destructive shadow-lg">
              <div className="text-3xl font-bold mb-1">3</div>
              <div className="text-xs font-mono text-muted-foreground">OVERRIDDEN</div>
            </Card>
          </div>

          {/* Anomaly List */}
          <Tabs defaultValue="pending" className="w-full">
            <TabsList className="border-2 border-foreground mb-6">
              <TabsTrigger value="pending" className="font-mono">PENDING</TabsTrigger>
              <TabsTrigger value="reviewed" className="font-mono">REVIEWED</TabsTrigger>
              <TabsTrigger value="high-risk" className="font-mono">HIGH RISK</TabsTrigger>
            </TabsList>

            <TabsContent value="pending">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <Card className="border-4 border-foreground shadow-lg overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow className="border-b-2 border-foreground">
                        <TableHead className="font-bold font-mono">SHEET ID</TableHead>
                        <TableHead className="font-bold font-mono">STUDENT</TableHead>
                        <TableHead className="font-bold font-mono">QUESTION</TableHead>
                        <TableHead className="font-bold font-mono">TYPE</TableHead>
                        <TableHead className="font-bold font-mono">CONFIDENCE</TableHead>
                        <TableHead className="font-bold font-mono">DETECTED</TableHead>
                        <TableHead className="font-bold font-mono">ACTIONS</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {mockAnomalies.filter(a => a.status === 'pending').map((anomaly) => (
                        <TableRow key={anomaly.id} className="border-b-2 border-muted">
                          <TableCell className="font-mono">{anomaly.sheetId}</TableCell>
                          <TableCell>
                            <div>
                              <div className="font-bold">{anomaly.studentName}</div>
                              <div className="text-xs font-mono text-muted-foreground">
                                {anomaly.rollNumber}
                              </div>
                            </div>
                          </TableCell>
                          <TableCell className="font-bold">Q{anomaly.questionNumber}</TableCell>
                          <TableCell>{getTypeBadge(anomaly.type)}</TableCell>
                          <TableCell>
                            <Badge
                              variant={anomaly.confidence < 70 ? 'secondary' : 'outline'}
                              className="border-2 border-foreground"
                            >
                              {anomaly.confidence.toFixed(1)}%
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className="border-2 border-foreground">
                              {anomaly.detectedAnswer}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex gap-2">
                              <Button size="sm" variant="outline" className="border-2 border-foreground">
                                <Eye className="w-4 h-4" />
                              </Button>
                              <Button size="sm" variant="outline" className="border-2 border-foreground">
                                <CheckCircle2 className="w-4 h-4" />
                              </Button>
                              <Button size="sm" variant="outline" className="border-2 border-foreground">
                                <XCircle className="w-4 h-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </Card>
              </motion.div>
            </TabsContent>

            <TabsContent value="reviewed">
              <Card className="p-12 border-4 border-foreground shadow-lg text-center">
                <div className="w-16 h-16 border-4 border-foreground bg-background mx-auto flex items-center justify-center mb-4">
                  <CheckCircle2 className="w-8 h-8" />
                </div>
                <h3 className="text-2xl font-bold mb-2">ALL CAUGHT UP!</h3>
                <p className="font-mono text-muted-foreground">
                  No reviewed anomalies at this time
                </p>
              </Card>
            </TabsContent>

            <TabsContent value="high-risk">
              <Card className="p-12 border-4 border-destructive shadow-lg text-center">
                <div className="w-16 h-16 border-4 border-foreground bg-background mx-auto flex items-center justify-center mb-4">
                  <AlertTriangle className="w-8 h-8" />
                </div>
                <h3 className="text-2xl font-bold mb-2">3 HIGH RISK ANOMALIES</h3>
                <p className="font-mono text-muted-foreground mb-6">
                  Require immediate attention and second review
                </p>
                <Button className="border-2 border-foreground shadow-md">
                  REVIEW HIGH RISK
                </Button>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </section>
    </div>
  );
};

export default AnomalyReview;
