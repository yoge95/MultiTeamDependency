import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { RequireAuth } from './components/auth/RequireAuth';
import { ErrorBoundary } from './components/ErrorBoundary';
import { LoginPage } from './pages/LoginPage';
import { QuestionPage } from './pages/QuestionPage';
import { AnswerPage } from './pages/AnswerPage';

/**
 * Root application component
 * Sets up React Router with authentication-aware routing
 */
function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<LoginPage />} />

            {/* Protected Routes */}
            <Route
              path="/question"
              element={
                <RequireAuth>
                  <QuestionPage />
                </RequireAuth>
              }
            />
            
            <Route
              path="/answer/:answerId"
              element={
                <RequireAuth>
                  <AnswerPage />
                </RequireAuth>
              }
            />

            {/* Home route redirects to question page */}
            <Route
              path="/"
              element={
                <RequireAuth>
                  <Navigate to="/question" replace />
                </RequireAuth>
              }
            />

            {/* Catch-all redirect to home */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
