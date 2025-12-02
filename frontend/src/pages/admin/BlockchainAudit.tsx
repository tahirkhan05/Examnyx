import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { 
  ArrowLeft, Shield, Search, Download, CheckCircle2, Lock, 
  Clock, Activity, Database, FileText, Scan, Brain, UserCheck, 
  Award, AlertTriangle, RefreshCw, Eye, ChevronDown, ChevronRight,
  Server, Layers, Hash, GitBranch, Users, BarChart3, Filter
} from 'lucide-react';

interface ChainEvent {
  id: string;
  type: 'batch_created' | 'sheet_uploaded' | 'ai_evaluation' | 'human_verification' | 'result_published' | 'key_locked' | 'dispute_raised';
  title: string;
  description: string;
  timestamp: string;
  status: 'completed' | 'processing' | 'pending' | 'flagged';
  batchId?: string;
  sheetCount?: number;
  operator?: string;
  blockHash: string;
  prevHash: string;
  blockIndex: number;
  details?: Record<string, string | number>;
}

const BlockchainAudit = () => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState<string>('all');
  const [expandedBlocks, setExpandedBlocks] = useState<Set<string>>(new Set());
  const [isVerifying, setIsVerifying] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Mock chain events - admin centric view
  const chainEvents: ChainEvent[] = [
    {
      id: '1',
      type: 'batch_created',
      title: 'BATCH INITIALIZED',
      description: 'New batch created with answer key locked on chain',
      timestamp: new Date(Date.now() - 2 * 3600000).toISOString(),
      status: 'completed',
      batchId: 'BATCH_2024_CS_MID_001',
      sheetCount: 250,
      operator: 'Admin: Dr. Smith',
      blockHash: '0x7f9fade1c0d57a7af66ab4ead79c2eb7b9c0d1e2',
      prevHash: '0x3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d',
      blockIndex: 12458,
      details: { 'Total Questions': 50, 'Subject': 'Computer Science', 'Exam Type': 'Mid-Term' }
    },
    {
      id: '2',
      type: 'key_locked',
      title: 'ANSWER KEY LOCKED',
      description: 'Official answer key immutably recorded on blockchain',
      timestamp: new Date(Date.now() - 1.9 * 3600000).toISOString(),
      status: 'completed',
      batchId: 'BATCH_2024_CS_MID_001',
      operator: 'System',
      blockHash: '0x9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b',
      prevHash: '0x7f9fade1c0d57a7af66ab4ead79c2eb7b9c0d1e2',
      blockIndex: 12459,
      details: { 'Key Version': 'v1.0', 'Encrypted': 'Yes', 'Signatures': 3 }
    },
    {
      id: '3',
      type: 'sheet_uploaded',
      title: 'BULK UPLOAD COMPLETE',
      description: '250 OMR sheets scanned and uploaded to system',
      timestamp: new Date(Date.now() - 1.5 * 3600000).toISOString(),
      status: 'completed',
      batchId: 'BATCH_2024_CS_MID_001',
      sheetCount: 250,
      operator: 'Scanner Station A',
      blockHash: '0xe5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4',
      prevHash: '0x9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b',
      blockIndex: 12460,
      details: { 'Processed': 250, 'Failed': 0, 'Quality Score': '98.5%' }
    },
    {
      id: '4',
      type: 'ai_evaluation',
      title: 'AI EVALUATION RUNNING',
      description: 'Multi-model bubble detection and confidence scoring',
      timestamp: new Date(Date.now() - 1 * 3600000).toISOString(),
      status: 'processing',
      batchId: 'BATCH_2024_CS_MID_001',
      sheetCount: 187,
      operator: 'AI Engine v2.1',
      blockHash: '0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b',
      prevHash: '0xe5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4',
      blockIndex: 12461,
      details: { 'Completed': 187, 'Remaining': 63, 'Avg Confidence': '96.2%' }
    },
    {
      id: '5',
      type: 'human_verification',
      title: 'HUMAN VERIFICATION QUEUE',
      description: 'Low confidence sheets flagged for manual review',
      timestamp: new Date(Date.now() - 0.5 * 3600000).toISOString(),
      status: 'pending',
      batchId: 'BATCH_2024_CS_MID_001',
      sheetCount: 12,
      operator: 'Pending Assignment',
      blockHash: '0x2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c',
      prevHash: '0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b',
      blockIndex: 12462,
      details: { 'Flagged Sheets': 12, 'Avg Confidence': '72.4%', 'Priority': 'High' }
    },
    {
      id: '6',
      type: 'dispute_raised',
      title: 'DISPUTE FLAGGED',
      description: 'Student challenge requires admin attention',
      timestamp: new Date(Date.now() - 0.25 * 3600000).toISOString(),
      status: 'flagged',
      batchId: 'BATCH_2024_CS_MID_001',
      operator: 'Student: John Doe (CS2024001)',
      blockHash: '0x3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d',
      prevHash: '0x2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c',
      blockIndex: 12463,
      details: { 'Question': 'Q15', 'Claimed Answer': 'B', 'Official Key': 'C', 'AI Verdict': 'Review Required' }
    },
  ];

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'batch_created': return Layers;
      case 'key_locked': return Lock;
      case 'sheet_uploaded': return Scan;
      case 'ai_evaluation': return Brain;
      case 'human_verification': return UserCheck;
      case 'result_published': return Award;
      case 'dispute_raised': return AlertTriangle;
      default: return FileText;
    }
  };

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'completed':
        return { color: 'bg-green-500', border: 'border-green-500', bg: 'bg-green-50 dark:bg-green-950/20', text: 'text-green-600' };
      case 'processing':
        return { color: 'bg-blue-500', border: 'border-blue-500', bg: 'bg-blue-50 dark:bg-blue-950/20', text: 'text-blue-600' };
      case 'pending':
        return { color: 'bg-yellow-500', border: 'border-yellow-500', bg: 'bg-yellow-50 dark:bg-yellow-950/20', text: 'text-yellow-600' };
      case 'flagged':
        return { color: 'bg-red-500', border: 'border-red-500', bg: 'bg-red-50 dark:bg-red-950/20', text: 'text-red-600' };
      default:
        return { color: 'bg-muted', border: 'border-muted', bg: 'bg-muted/20', text: 'text-muted-foreground' };
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return {
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
      time: date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true })
    };
  };

  const getTimeDifference = (timestamp: string) => {
    const then = new Date(timestamp).getTime();
    const now = currentTime.getTime();
    const diff = now - then;
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  };

  const toggleBlockExpansion = (id: string) => {
    const newExpanded = new Set(expandedBlocks);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedBlocks(newExpanded);
  };

  const handleVerifyChain = async () => {
    setIsVerifying(true);
    // Simulate verification
    await new Promise(resolve => setTimeout(resolve, 2000));
    setIsVerifying(false);
  };

  const filteredEvents = chainEvents.filter(event => {
    if (selectedFilter !== 'all' && event.status !== selectedFilter) return false;
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        event.title.toLowerCase().includes(query) ||
        event.batchId?.toLowerCase().includes(query) ||
        event.blockHash.toLowerCase().includes(query) ||
        event.operator?.toLowerCase().includes(query)
      );
    }
    return true;
  });

  // Stats calculations
  const totalBlocks = chainEvents.length;
  const completedBlocks = chainEvents.filter(e => e.status === 'completed').length;
  const pendingActions = chainEvents.filter(e => e.status === 'pending' || e.status === 'flagged').length;
  const processingBlocks = chainEvents.filter(e => e.status === 'processing').length;

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
            <div className="flex items-center gap-3">
              <Database className="w-8 h-8" />
              <div>
                <h1 className="text-4xl font-bold">BLOCKCHAIN AUDIT TRAIL</h1>
                <p className="text-sm font-mono text-muted-foreground mt-1">
                  System-wide chain monitoring • Real-time event tracking
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="border-2 border-green-500 text-green-600 px-3 py-1">
                <Activity className="w-3 h-3 mr-1 animate-pulse" />
                CHAIN ACTIVE
              </Badge>
            </div>
          </div>
        </div>
      </header>

      <section className="py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
          
          {/* Stats Overview */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-4"
          >
            <Card className="p-4 border-4 border-foreground shadow-lg">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-chart-1/20 rounded-lg flex items-center justify-center">
                  <Layers className="w-6 h-6 text-chart-1" />
                </div>
                <div>
                  <p className="text-2xl font-bold">12,463</p>
                  <p className="text-xs font-mono text-muted-foreground">TOTAL BLOCKS</p>
                </div>
              </div>
            </Card>
            <Card className="p-4 border-4 border-green-500 shadow-lg">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-green-500/20 rounded-lg flex items-center justify-center">
                  <CheckCircle2 className="w-6 h-6 text-green-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{completedBlocks}</p>
                  <p className="text-xs font-mono text-muted-foreground">VERIFIED</p>
                </div>
              </div>
            </Card>
            <Card className="p-4 border-4 border-blue-500 shadow-lg">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center">
                  <RefreshCw className={`w-6 h-6 text-blue-500 ${processingBlocks > 0 ? 'animate-spin' : ''}`} />
                </div>
                <div>
                  <p className="text-2xl font-bold">{processingBlocks}</p>
                  <p className="text-xs font-mono text-muted-foreground">PROCESSING</p>
                </div>
              </div>
            </Card>
            <Card className="p-4 border-4 border-yellow-500 shadow-lg">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-yellow-500/20 rounded-lg flex items-center justify-center">
                  <AlertTriangle className="w-6 h-6 text-yellow-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{pendingActions}</p>
                  <p className="text-xs font-mono text-muted-foreground">NEEDS ACTION</p>
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Chain Integrity Status */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card className="p-6 border-4 border-green-500 bg-green-50 dark:bg-green-950/20 shadow-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 rounded-full bg-green-500 flex items-center justify-center">
                    <Shield className="w-8 h-8 text-white" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-green-700 dark:text-green-400">CHAIN INTEGRITY VERIFIED</h2>
                    <p className="text-sm text-green-600 dark:text-green-500 font-mono">
                      All blocks validated • No tampering detected • Last check: {currentTime.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Button 
                    variant="outline" 
                    className="border-2 border-green-600 text-green-600 hover:bg-green-100"
                    onClick={handleVerifyChain}
                    disabled={isVerifying}
                  >
                    {isVerifying ? (
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Shield className="w-4 h-4 mr-2" />
                    )}
                    {isVerifying ? 'VERIFYING...' : 'VERIFY NOW'}
                  </Button>
                  <Button variant="outline" className="border-2 border-green-600 text-green-600 hover:bg-green-100">
                    <Download className="w-4 h-4 mr-2" />
                    EXPORT REPORT
                  </Button>
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Search and Filter */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="p-4 border-4 border-foreground shadow-lg">
              <div className="flex flex-wrap gap-4 items-center">
                <div className="flex-1 min-w-[300px]">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      placeholder="Search by batch ID, block hash, operator..."
                      className="pl-10 border-2 border-foreground"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Filter className="w-4 h-4 text-muted-foreground" />
                  <div className="flex gap-1">
                    {['all', 'completed', 'processing', 'pending', 'flagged'].map((filter) => (
                      <Button
                        key={filter}
                        size="sm"
                        variant={selectedFilter === filter ? 'default' : 'outline'}
                        className={`border-2 text-xs ${selectedFilter === filter ? '' : 'border-foreground'}`}
                        onClick={() => setSelectedFilter(filter)}
                      >
                        {filter.toUpperCase()}
                      </Button>
                    ))}
                  </div>
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Timeline Events */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card className="p-6 border-4 border-foreground shadow-lg">
              <div className="flex items-center gap-2 mb-6">
                <Clock className="w-5 h-5" />
                <h3 className="text-xl font-bold">CHAIN EVENT TIMELINE</h3>
                <Badge variant="secondary" className="ml-2">
                  {filteredEvents.length} events
                </Badge>
                <span className="ml-auto text-xs font-mono text-muted-foreground">
                  Real-time updates • Click to expand
                </span>
              </div>

              <div className="relative">
                {filteredEvents.map((event, index) => {
                  const IconComponent = getEventIcon(event.type);
                  const statusConfig = getStatusConfig(event.status);
                  const time = formatTimestamp(event.timestamp);
                  const isLast = index === filteredEvents.length - 1;
                  const isExpanded = expandedBlocks.has(event.id);
                  
                  return (
                    <motion.div
                      key={event.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="relative pl-14 pb-6"
                    >
                      {/* Vertical Line */}
                      {!isLast && (
                        <div className={`absolute left-[22px] top-12 w-0.5 h-full ${statusConfig.color}`} />
                      )}
                      
                      {/* Step Icon */}
                      <div className={`absolute left-0 w-11 h-11 rounded-lg flex items-center justify-center border-2 ${statusConfig.color} ${statusConfig.border} text-white`}>
                        {event.status === 'completed' ? (
                          <CheckCircle2 className="w-5 h-5" />
                        ) : event.status === 'processing' ? (
                          <RefreshCw className="w-5 h-5 animate-spin" />
                        ) : (
                          <IconComponent className="w-5 h-5" />
                        )}
                      </div>

                      {/* Event Content */}
                      <div 
                        className={`border-2 rounded-lg overflow-hidden cursor-pointer transition-all hover:shadow-md ${statusConfig.border} ${statusConfig.bg}`}
                        onClick={() => toggleBlockExpansion(event.id)}
                      >
                        {/* Header */}
                        <div className="p-4">
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <IconComponent className="w-4 h-4" />
                                <h4 className="font-bold">{event.title}</h4>
                                <Badge 
                                  variant="outline" 
                                  className={`text-xs ${statusConfig.border} ${statusConfig.text}`}
                                >
                                  {event.status === 'completed' && '✓ DONE'}
                                  {event.status === 'processing' && '◉ IN PROGRESS'}
                                  {event.status === 'pending' && '◌ PENDING'}
                                  {event.status === 'flagged' && '⚠ FLAGGED'}
                                </Badge>
                              </div>
                              <p className="text-sm text-muted-foreground mb-2">{event.description}</p>
                              <div className="flex flex-wrap gap-2 text-xs">
                                {event.batchId && (
                                  <span className="font-mono bg-muted/50 px-2 py-0.5 rounded">
                                    {event.batchId}
                                  </span>
                                )}
                                {event.sheetCount && (
                                  <span className="font-mono bg-muted/50 px-2 py-0.5 rounded">
                                    {event.sheetCount} sheets
                                  </span>
                                )}
                                {event.operator && (
                                  <span className="font-mono bg-muted/50 px-2 py-0.5 rounded flex items-center gap-1">
                                    <Users className="w-3 h-3" />
                                    {event.operator}
                                  </span>
                                )}
                              </div>
                            </div>
                            <div className="text-right flex-shrink-0">
                              <p className="text-sm font-bold">{time.date}</p>
                              <p className="text-xs font-mono text-muted-foreground">{time.time}</p>
                              <p className={`text-xs mt-1 ${statusConfig.text}`}>
                                {getTimeDifference(event.timestamp)}
                              </p>
                            </div>
                            <div className="flex-shrink-0">
                              {isExpanded ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                            </div>
                          </div>
                        </div>

                        {/* Expanded Details */}
                        {isExpanded && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            className="border-t border-muted"
                          >
                            <div className="p-4 bg-muted/20 space-y-3">
                              {/* Block Info */}
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                <div className="p-3 bg-background rounded-lg border">
                                  <div className="flex items-center gap-2 text-xs font-mono text-muted-foreground mb-1">
                                    <Hash className="w-3 h-3" />
                                    BLOCK HASH
                                  </div>
                                  <p className="font-mono text-xs break-all">{event.blockHash}</p>
                                </div>
                                <div className="p-3 bg-background rounded-lg border">
                                  <div className="flex items-center gap-2 text-xs font-mono text-muted-foreground mb-1">
                                    <GitBranch className="w-3 h-3" />
                                    PREVIOUS HASH
                                  </div>
                                  <p className="font-mono text-xs break-all">{event.prevHash}</p>
                                </div>
                              </div>

                              {/* Event Details */}
                              {event.details && (
                                <div className="p-3 bg-background rounded-lg border">
                                  <div className="flex items-center gap-2 text-xs font-mono text-muted-foreground mb-2">
                                    <BarChart3 className="w-3 h-3" />
                                    EVENT DETAILS
                                  </div>
                                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                                    {Object.entries(event.details).map(([key, value]) => (
                                      <div key={key} className="text-xs">
                                        <span className="text-muted-foreground">{key}:</span>
                                        <span className="font-bold ml-1">{value}</span>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Actions */}
                              <div className="flex gap-2">
                                <Button size="sm" variant="outline" className="text-xs border">
                                  <Eye className="w-3 h-3 mr-1" />
                                  VIEW FULL BLOCK
                                </Button>
                                <Button size="sm" variant="outline" className="text-xs border">
                                  <Download className="w-3 h-3 mr-1" />
                                  EXPORT
                                </Button>
                                {event.status === 'flagged' && (
                                  <Button size="sm" className="text-xs bg-red-500 hover:bg-red-600 text-white">
                                    <AlertTriangle className="w-3 h-3 mr-1" />
                                    REVIEW DISPUTE
                                  </Button>
                                )}
                                {event.status === 'pending' && (
                                  <Button size="sm" className="text-xs bg-yellow-500 hover:bg-yellow-600 text-white">
                                    <UserCheck className="w-3 h-3 mr-1" />
                                    ASSIGN REVIEWER
                                  </Button>
                                )}
                              </div>
                            </div>
                          </motion.div>
                        )}

                        {/* Block Index Footer */}
                        <div className="px-4 py-2 bg-muted/30 border-t border-muted flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Server className="w-3 h-3 text-muted-foreground" />
                            <span className="text-xs font-mono text-muted-foreground">
                              Block #{event.blockIndex}
                            </span>
                          </div>
                          <Badge variant="secondary" className="text-xs">
                            <Shield className="w-3 h-3 mr-1" />
                            IMMUTABLE
                          </Badge>
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </Card>
          </motion.div>

          {/* Security Info */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card className="p-6 border-4 border-chart-4 shadow-lg">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Shield className="w-5 h-5" />
                CHAIN SECURITY FEATURES
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="flex items-start gap-3 p-3 bg-muted/30 rounded-lg">
                  <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-bold text-sm">SHA-256 Hashing</p>
                    <p className="text-xs text-muted-foreground">Cryptographic security on every block</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 bg-muted/30 rounded-lg">
                  <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-bold text-sm">Multi-Signature</p>
                    <p className="text-xs text-muted-foreground">AI + Human + Admin approval required</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 bg-muted/30 rounded-lg">
                  <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-bold text-sm">Immutable Ledger</p>
                    <p className="text-xs text-muted-foreground">Once recorded, data cannot be altered</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 bg-muted/30 rounded-lg">
                  <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-bold text-sm">Full Audit Trail</p>
                    <p className="text-xs text-muted-foreground">Complete history of every operation</p>
                  </div>
                </div>
              </div>
            </Card>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default BlockchainAudit;
