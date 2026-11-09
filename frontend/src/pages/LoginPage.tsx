import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import sharedConfig from '../../../shared_config.json';

/**
 * Login page matching wireframe design specifications
 * Implements gradient background, centered card layout, form controls, and SSO button
 */
export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  // Get field names from shared config
  const [email, password] = sharedConfig.auth.login_request.field_names;

  // Form state - defaults match seed data credentials
  const [formData, setFormData] = useState({
    [email]: 'admin@example.com',
    [password]: 'admin123',
  });
  const [rememberMe, setRememberMe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await login(formData[email], formData[password]);
      
      // Redirect to intended destination or home
      const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/';
      navigate(from, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [field]: e.target.value }));
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6" style={{
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-12">
        {/* Logo Section */}
        <div className="text-center mb-8">
          <div
            className="w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
          >
            <svg
              className="w-8 h-8 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
              />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Welcome Back</h1>
          <p className="text-gray-600">Sign in to access your knowledge assistant</p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm">
            {error}
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit}>
          {/* Email Field */}
          <div className="mb-6">
            <label htmlFor="email" className="block text-sm font-semibold text-gray-800 mb-2">
              Email Address
            </label>
            <input
              type="email"
              id="email"
              value={formData[email]}
              onChange={handleInputChange(email)}
              placeholder="you@company.com"
              required
              className="w-full px-4 py-3.5 text-base border-2 border-gray-200 rounded-lg transition-all focus:outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
            />
          </div>

          {/* Password Field */}
          <div className="mb-6">
            <label htmlFor="password" className="block text-sm font-semibold text-gray-800 mb-2">
              Password
            </label>
            <input
              type="password"
              id="password"
              value={formData[password]}
              onChange={handleInputChange(password)}
              placeholder="Enter your password"
              required
              className="w-full px-4 py-3.5 text-base border-2 border-gray-200 rounded-lg transition-all focus:outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
            />
          </div>

          {/* Remember Me & Forgot Password */}
          <div className="flex justify-between items-center mb-6 text-sm">
            <label className="flex items-center gap-2 text-gray-700 cursor-pointer">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              <span>Remember me</span>
            </label>
            <a href="#" className="text-indigo-600 hover:underline font-medium">
              Forgot password?
            </a>
          </div>

          {/* Sign In Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-4 px-6 text-base font-semibold text-white rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:transform hover:-translate-y-0.5 hover:shadow-xl mb-4"
            style={{
              background: isLoading ? '#9ca3af' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
            }}
          >
            {isLoading ? 'Signing In...' : 'Sign In'}
          </button>
        </form>

        {/* Divider */}
        <div className="relative my-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-200"></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-4 bg-white text-gray-500">or continue with</span>
          </div>
        </div>

        {/* SSO Button */}
        <button
          type="button"
          className="w-full py-3.5 px-6 text-base font-medium text-gray-800 bg-white border-2 border-gray-200 rounded-lg transition-all hover:bg-gray-50 hover:border-gray-300 flex items-center justify-center gap-3"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"
            />
          </svg>
          Sign in with SSO
        </button>

        {/* Help Text */}
        <p className="text-center mt-6 text-sm text-gray-600">
          Need help?{' '}
          <a href="#" className="text-indigo-600 hover:underline font-medium">
            Contact Support
          </a>
        </p>
      </div>
    </div>
  );
}
