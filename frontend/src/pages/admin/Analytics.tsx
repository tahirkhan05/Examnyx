import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, TrendingUp, AlertTriangle, CheckCircle2, Lock } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const Analytics = () => {
  const questionData = Array.from({ length: 25 }, (_, i) => ({
    question: i + 1,
    correctRate: Math.random() * 40 + 60,
    anomalyCount: Math.floor(Math.random() * 10),
    avgConfidence: Math.random() * 20 + 80,
  }));

  const riskQuestions = questionData
    .filter(q => q.correctRate < 70 || q.anomalyCount > 5)
    .sort((a, b) => a.correctRate - b.correctRate)
    .slice(0, 5);

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
          <h1 className="text-4xl font-bold">ANALYTICS & PUBLISHING</h1>
          <p className="text-sm font-mono text-muted-foreground mt-2">
            Question-wise analytics, risk flags, and multi-sign result publishing
          </p>
        </div>
      </header>

      <section className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
          {/* Question Analytics */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <Card className="p-8 border-4 border-chart-1 shadow-lg">
              <h3 className="text-2xl font-bold mb-6">QUESTION-WISE CORRECT RATE</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={questionData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--muted))" />
                  <XAxis
                    dataKey="question"
                    stroke="hsl(var(--foreground))"
                    tick={{ fill: 'hsl(var(--foreground))' }}
                  />
                  <YAxis
                    stroke="hsl(var(--foreground))"
                    tick={{ fill: 'hsl(var(--foreground))' }}
                    label={{ value: 'Correct Rate (%)', angle: -90, position: 'insideLeft' }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '2px solid hsl(var(--foreground))',
                    }}
                  />
                  <Bar dataKey="correctRate" fill="hsl(var(--chart-1))">
                    {questionData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={
                          entry.correctRate < 70
                            ? 'hsl(var(--destructive))'
                            : 'hsl(var(--chart-1))'
                        }
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </motion.div>

          {/* Risk Flags */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="p-8 border-4 border-chart-3 shadow-lg">
              <h3 className="text-2xl font-bold mb-6 flex items-center gap-3">
                <AlertTriangle className="w-6 h-6" />
                KEY RISK FLAGS
              </h3>
              <div className="space-y-3">
                {riskQuestions.map((q) => (
                  <div key={q.question} className="border-2 border-muted p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="font-bold font-mono">QUESTION {q.question}</span>
                        <div className="text-sm font-mono text-muted-foreground mt-1">
                          {q.anomalyCount} anomalies detected
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge
                          variant={q.correctRate < 70 ? 'destructive' : 'secondary'}
                          className="border-2 border-foreground mb-1"
                        >
                          {q.correctRate.toFixed(1)}% CORRECT
                        </Badge>
                        <div className="text-xs font-mono text-muted-foreground">
                          {q.avgConfidence.toFixed(1)}% confidence
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </motion.div>

          {/* Publishing Gate */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card className="p-8 border-4 border-chart-2 shadow-lg">
              <h3 className="text-2xl font-bold mb-6 flex items-center gap-3">
                <Lock className="w-6 h-6" />
                PUBLISHING CHECKLIST
              </h3>
              <div className="space-y-3 mb-8">
                <div className="flex items-center gap-3 p-3 border-2 border-muted">
                  <CheckCircle2 className="w-5 h-5 text-chart-2" />
                  <span className="font-mono">Answer key locked and verified</span>
                </div>
                <div className="flex items-center gap-3 p-3 border-2 border-muted">
                  <CheckCircle2 className="w-5 h-5 text-chart-2" />
                  <span className="font-mono">All OMR sheets processed</span>
                </div>
                <div className="flex items-center gap-3 p-3 border-2 border-chart-3">
                  <AlertTriangle className="w-5 h-5" />
                  <span className="font-mono">32 anomalies pending review</span>
                </div>
                <div className="flex items-center gap-3 p-3 border-2 border-muted">
                  <CheckCircle2 className="w-5 h-5 text-chart-2" />
                  <span className="font-mono">Blockchain verification complete</span>
                </div>
                <div className="flex items-center gap-3 p-3 border-2 border-muted">
                  <Lock className="w-5 h-5" />
                  <span className="font-mono">Awaiting multi-sign approval (1/3)</span>
                </div>
              </div>

              <div className="flex gap-4">
                <Button
                  className="flex-1 border-2 border-foreground shadow-md"
                  disabled
                >
                  PUBLISH RESULTS
                </Button>
                <Button
                  variant="outline"
                  className="flex-1 border-2 border-foreground shadow-md"
                >
                  GENERATE QR CODES
                </Button>
              </div>

              <div className="mt-6 p-4 border-2 border-muted bg-muted/20">
                <p className="text-xs font-mono text-muted-foreground">
                  ⚠ Complete all anomaly reviews before publishing results
                </p>
              </div>
            </Card>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default Analytics;
