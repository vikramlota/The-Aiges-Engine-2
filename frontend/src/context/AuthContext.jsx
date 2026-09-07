import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi, getToken, setToken } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setTokenState] = useState(getToken());
  const [loading, setLoading] = useState(true);

  // Validate session on app mount
  useEffect(() => {
    async function checkAuth() {
      const storedToken = getToken();
      if (!storedToken) {
        setUser(null);
        setLoading(false);
        return;
      }
      try {
        const userData = await authApi.getMe();
        setUser(userData);
      } catch (err) {
        setUser(null);
        setToken(null);
        setTokenState(null);
      } finally {
        setLoading(false);
      }
    }

    checkAuth();

    // Listen for global logout event dispatched by 401 interceptor
    const handleLogoutEvent = () => {
      setUser(null);
      setTokenState(null);
    };
    window.addEventListener('auth:logout', handleLogoutEvent);
    return () => window.removeEventListener('auth:logout', handleLogoutEvent);
  }, []);

  const login = async (email, password) => {
    const data = await authApi.login(email, password);
    setTokenState(data.access_token);
    const userData = await authApi.getMe();
    setUser(userData);
    return userData;
  };

  const signup = async (email, password) => {
    await authApi.signup(email, password);
    return login(email, password);
  };

  const logout = () => {
    authApi.logout();
    setUser(null);
    setTokenState(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, signup, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
