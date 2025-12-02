import { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuthStore } from '@/store/authStore';
import { toast } from 'sonner';
import { ShieldCheck, ArrowLeft } from 'lucide-react';

const AdminLogin = () => {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await login(formData.email, formData.password, 'institution_admin');
      toast.success('Login successful!');
      navigate('/admin/dashboard');
    } catch (error) {
      toast.error('Invalid credentials. Try: admin@example.com / admin123');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <Link to="/">
          <Button variant="outline" size="sm" className="mb-6 border-2 border-foreground">
            <ArrowLeft className="w-4 h-4 mr-2" />
            BACK TO HOME
          </Button>
        </Link>

        <div className="border-4 border-foreground bg-card p-8 shadow-xl">
          <div className="flex items-center justify-center mb-8">
            <div className="w-16 h-16 border-4 border-foreground bg-background flex items-center justify-center">
              <ShieldCheck className="w-8 h-8" />
            </div>
          </div>

          <h1 className="text-3xl font-bold text-center mb-2">ADMIN LOGIN</h1>
          <p className="text-center text-muted-foreground font-mono text-sm mb-8">
            Institution & Exam Center Portal
          </p>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <Label htmlFor="email" className="font-mono">EMAIL / EMPLOYEE ID</Label>
              <Input
                id="email"
                type="text"
                placeholder="admin@example.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
                className="mt-2 border-2 border-foreground"
              />
            </div>

            <div>
              <Label htmlFor="password" className="font-mono">PASSWORD</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
                className="mt-2 border-2 border-foreground"
              />
            </div>

            <Button
              type="submit"
              className="w-full border-4 border-foreground shadow-md"
              disabled={loading}
            >
              {loading ? 'LOGGING IN...' : 'LOGIN'}
            </Button>
          </form>

          <div className="mt-6 p-4 border-2 border-muted bg-muted/20">
            <p className="text-xs font-mono text-muted-foreground">
              Demo credentials:<br />
              Admin: admin@example.com / admin123<br />
              Operator: operator@example.com / operator123
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default AdminLogin;
