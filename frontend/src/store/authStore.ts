import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { AuthState, User, UserRole } from '@/types';

// Mock users for demo
const mockUsers: Record<string, { password: string; user: User }> = {
  'student@example.com': {
    password: 'student123',
    user: {
      id: '1',
      name: 'John Doe',
      email: 'student@example.com',
      role: 'student',
      rollNumber: 'CS2024001',
      phoneNumber: '+1234567890',
    },
  },
  'admin@example.com': {
    password: 'admin123',
    user: {
      id: '2',
      name: 'Jane Smith',
      email: 'admin@example.com',
      role: 'institution_admin',
      employeeId: 'EMP001',
      department: 'Computer Science',
    },
  },
  'operator@example.com': {
    password: 'operator123',
    user: {
      id: '3',
      name: 'Mike Johnson',
      email: 'operator@example.com',
      role: 'exam_center_operator',
      employeeId: 'EMP002',
      department: 'Exam Center',
    },
  },
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: async (email: string, password: string, role: UserRole) => {
        // Simulate API delay
        await new Promise((resolve) => setTimeout(resolve, 1000));

        const mockUser = mockUsers[email];

        if (!mockUser || mockUser.password !== password) {
          throw new Error('Invalid credentials');
        }

        if (
          (role === 'student' && mockUser.user.role !== 'student') ||
          (role !== 'student' && mockUser.user.role === 'student')
        ) {
          throw new Error('Invalid role for this user');
        }

        const token = `mock_token_${Date.now()}`;

        set({
          user: mockUser.user,
          token,
          isAuthenticated: true,
        });
      },

      logout: () => {
        set({
          user: null,
          token: null,
          isAuthenticated: false,
        });
      },
    }),
    {
      name: 'auth-storage',
    }
  )
);
