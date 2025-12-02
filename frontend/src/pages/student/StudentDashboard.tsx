import { motion } from 'framer-motion';
import { useAuthStore } from '@/store/authStore';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { FileText, Upload, AlertCircle, Shield, LogOut } from 'lucide-react';

const StudentDashboard = () => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const cards = [
    {
      title: 'RESULT SUMMARY',
      icon: FileText,
      description: 'View your exam results, scores, and performance analytics',
      route: '/student/results',
      color: 'border-chart-1',
    },
    {
      title: 'OMR VERIFICATION',
      icon: Upload,
      description: 'Upload OMR sheets and track evaluation with explainable AI',
      route: '/student/omr-verification',
      color: 'border-chart-2',
    },
    {
      title: 'CHALLENGE & DISPUTE',
      icon: AlertCircle,
      description: 'Raise objections and track your dispute status',
      route: '/student/challenges',
      color: 'border-chart-3',
    },
    {
      title: 'BLOCKCHAIN AUDIT',
      icon: Shield,
      description: 'Verify result authenticity with blockchain proof',
      route: '/student/blockchain',
      color: 'border-chart-4',
    },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b-4 border-foreground bg-card">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">EXAMNYX</h1>
              <p className="text-sm font-mono text-muted-foreground mt-1">STUDENT PORTAL</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right hidden sm:block">
                <p className="font-bold">{user?.name}</p>
                <p className="text-sm font-mono text-muted-foreground">{user?.rollNumber}</p>
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

      {/* Welcome Section */}
      <section className="border-b-4 border-foreground bg-muted/20 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="text-4xl font-bold mb-2">WELCOME BACK, {user?.name?.split(' ')[0].toUpperCase()}</h2>
            <p className="text-lg font-mono text-muted-foreground">
              Access your exam results and verification tools
            </p>
          </motion.div>
        </div>
      </section>

      {/* Main Content */}
      <section className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
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
                  <div className="mb-6">
                    <div className="w-16 h-16 border-4 border-foreground bg-background flex items-center justify-center">
                      <card.icon className="w-8 h-8" />
                    </div>
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

export default StudentDashboard;
