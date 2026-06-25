import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, App as AntApp, Spin } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import theme from './theme';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import AppLayout from './components/AppLayout';

// Pages
import Dashboard from './pages/Dashboard';
import ClassesPage from './pages/DataManagement/ClassesPage';
import TeachersPage from './pages/DataManagement/TeachersPage';
import CoursesPage from './pages/DataManagement/CoursesPage';
import ClassroomsPage from './pages/DataManagement/ClassroomsPage';
import ImportPage from './pages/DataManagement/ImportPage';
import ConstraintsPage from './pages/Scheduling/ConstraintsPage';
import EnginePage from './pages/Scheduling/EnginePage';
import ConflictsPage from './pages/Scheduling/ConflictsPage';
import TimetableView from './pages/TimetableView';
import ReportsPage from './pages/ReportsPage';
import ExportPage from './pages/ExportPage';
import Login from './pages/Login';
import Register from './pages/Register';

// 路由守卫：未登录重定向到登录页
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

export default function App() {
  return (
    <ConfigProvider theme={theme} locale={zhCN}>
      <AntApp>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              {/* 公开路由 */}
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />

              {/* 受保护路由（需要登录） */}
              <Route
                element={
                  <ProtectedRoute>
                    <AppLayout />
                  </ProtectedRoute>
                }
              >
                <Route path="/" element={<Dashboard />} />
                <Route path="/data/classes" element={<ClassesPage />} />
                <Route path="/data/teachers" element={<TeachersPage />} />
                <Route path="/data/courses" element={<CoursesPage />} />
                <Route path="/data/classrooms" element={<ClassroomsPage />} />
                <Route path="/data/import" element={<ImportPage />} />
                <Route path="/schedule/constraints" element={<ConstraintsPage />} />
                <Route path="/schedule/engine" element={<EnginePage />} />
                <Route path="/schedule/conflicts" element={<ConflictsPage />} />
                <Route path="/timetable" element={<TimetableView />} />
                <Route path="/reports" element={<ReportsPage />} />
                <Route path="/export" element={<ExportPage />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </AntApp>
    </ConfigProvider>
  );
}
