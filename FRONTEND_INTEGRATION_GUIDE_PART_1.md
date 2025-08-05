# 🌾 AgriTech Platform - Frontend Integration Guide

## Complete Registration, Login & Role-Based Dashboard Implementation

**Version:** 6.0.0  
**Date:** August 5, 2025  
**API Base URL:** `http://localhost:8000/api/v6`  
**Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📋 Table of Contents

1. [🚀 Quick Start Setup](#-quick-start-setup)
2. [🔐 Authentication System](#-authentication-system)
3. [👥 User Registration Flow](#-user-registration-flow)
4. [🔑 Login Implementation](#-login-implementation)
5. [🛡️ Role-Based Access Control](#️-role-based-access-control)
6. [📊 Dashboard Components](#-dashboard-components)
7. [🔧 Utility Functions](#-utility-functions)
8. [📱 State Management](#-state-management)
9. [🌐 API Integration Examples](#-api-integration-examples)
10. [🎯 Next Steps & Extension Points](#-next-steps--extension-points)

---

## 🚀 Quick Start Setup

### Prerequisites

- ✅ **CORS Configured**: Any localhost port can access the API
- ✅ **Backend Running**: AgriTech API on `http://localhost:8000`
- ✅ **Frontend Framework**: React/Vue/Angular/Next.js (any localhost port)

### Environment Configuration

```javascript
// config/api.js
export const API_CONFIG = {
  BASE_URL: "http://localhost:8000/api/v6",
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,

  // CORS is configured for any localhost port
  CORS_ENABLED: true,
  CREDENTIALS: "include",

  // Available endpoints
  ENDPOINTS: {
    AUTH: "/auth",
    ADMIN: "/admin",
    COMMODITIES: "/commodities",
    BIDDING: "/bidding",
    SELLER: "/seller",
    ML: "/ml",
    PRICE_TRACKING: "/price-tracking",
    MOBILE: "/mobile",
    GENERAL: "/general",
  },
};

// HTTP Client Configuration
export const httpClient = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  timeout: API_CONFIG.TIMEOUT,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});
```

---

## 🔐 Authentication System

### Core Authentication Types

```typescript
// types/auth.ts
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_verified: boolean;
  is_active: boolean;
  avatar?: {
    url: string;
  };
  created_at: string;
  last_login?: string;
}

export enum UserRole {
  FARMER = "FARMER",
  TRADER = "TRADER",
  ADMIN = "ADMIN",
}

// Note: There is NO "AUCTIONEER" role in this system
// Farmers manage their own commodity auctions directly

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthResponse {
  message: string;
  data: {
    user: User;
    tokens: AuthTokens;
  };
}
```

### Authentication Service

```javascript
// services/authService.js
class AuthService {
  constructor() {
    this.baseURL = API_CONFIG.BASE_URL + API_CONFIG.ENDPOINTS.AUTH;
    this.setupInterceptors();
  }

  // Setup HTTP interceptors for token management
  setupInterceptors() {
    // Request interceptor - Add auth token
    httpClient.interceptors.request.use(
      (config) => {
        const token = this.getAccessToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor - Handle token refresh
    httpClient.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          const refreshed = await this.refreshTokens();
          if (refreshed) {
            // Retry original request
            return httpClient.request(error.config);
          } else {
            this.logout();
            window.location.href = "/login";
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // Token management
  getAccessToken() {
    return localStorage.getItem("access_token");
  }

  getRefreshToken() {
    return localStorage.getItem("refresh_token");
  }

  setTokens(tokens) {
    localStorage.setItem("access_token", tokens.access_token);
    localStorage.setItem("refresh_token", tokens.refresh_token);
  }

  clearTokens() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
  }

  // Check if user is authenticated
  isAuthenticated() {
    const token = this.getAccessToken();
    if (!token) return false;

    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      return payload.exp * 1000 > Date.now();
    } catch {
      return false;
    }
  }

  // Get current user from storage
  getCurrentUser() {
    try {
      const userStr = localStorage.getItem("user");
      return userStr ? JSON.parse(userStr) : null;
    } catch {
      return null;
    }
  }
}

export const authService = new AuthService();
```

---

## 👥 User Registration Flow

### 1. Registration Form Component

```jsx
// components/auth/RegisterForm.jsx
import React, { useState } from "react";
import { authService } from "../../services/authService";

const RegisterForm = () => {
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    confirmPassword: "",
    role: "FARMER",
    terms_agreement: false,
    phone_number: "",
    upi_id: "",
    bank_account: "",
    ifsc_code: "",
  });

  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1); // Multi-step registration

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));

    // Clear error when user starts typing
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: "" }));
    }
  };

  const validateStep1 = () => {
    const newErrors = {};

    if (!formData.first_name.trim()) {
      newErrors.first_name = "First name is required";
    }

    if (!formData.last_name.trim()) {
      newErrors.last_name = "Last name is required";
    }

    if (!formData.email) {
      newErrors.email = "Email is required";
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = "Email is invalid";
    }

    if (!formData.password) {
      newErrors.password = "Password is required";
    } else if (formData.password.length < 8) {
      newErrors.password = "Password must be at least 8 characters";
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match";
    }

    if (!formData.terms_agreement) {
      newErrors.terms_agreement = "You must agree to terms and conditions";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateStep2 = () => {
    const newErrors = {};

    if (formData.ifsc_code && formData.ifsc_code.length !== 11) {
      newErrors.ifsc_code = "IFSC code must be exactly 11 characters";
    }

    if (formData.bank_account && !/^\d+$/.test(formData.bank_account)) {
      newErrors.bank_account = "Bank account must contain only digits";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNextStep = () => {
    if (step === 1 && validateStep1()) {
      setStep(2);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateStep2()) return;

    setLoading(true);
    try {
      const response = await authService.register(formData);

      // Registration successful - redirect to verification
      alert(
        "Registration successful! Please check your email for verification."
      );
      // Redirect to email verification page
      window.location.href = `/verify-email?email=${encodeURIComponent(
        formData.email
      )}`;
    } catch (error) {
      setErrors({
        submit:
          error.response?.data?.detail ||
          "Registration failed. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="register-form">
      <h2>Join AgriTech Platform</h2>

      {/* Progress Indicator */}
      <div className="progress-steps">
        <div className={`step ${step >= 1 ? "active" : ""}`}>
          <span>1</span> Basic Info
        </div>
        <div className={`step ${step >= 2 ? "active" : ""}`}>
          <span>2</span> Payment Details
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        {step === 1 && (
          <div className="step-1">
            {/* Role Selection */}
            <div className="form-group">
              <label>Register as:</label>
              <div className="role-selection">
                <label className="role-option">
                  <input
                    type="radio"
                    name="role"
                    value="FARMER"
                    checked={formData.role === "FARMER"}
                    onChange={handleInputChange}
                  />
                  <span>🌾 Farmer - Sell your produce</span>
                </label>
                <label className="role-option">
                  <input
                    type="radio"
                    name="role"
                    value="TRADER"
                    checked={formData.role === "TRADER"}
                    onChange={handleInputChange}
                  />
                  <span>🏪 Trader - Buy agricultural products</span>
                </label>
              </div>
            </div>

            {/* Basic Information */}
            <div className="form-row">
              <div className="form-group">
                <label>First Name *</label>
                <input
                  type="text"
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleInputChange}
                  className={errors.first_name ? "error" : ""}
                  placeholder="Enter your first name"
                />
                {errors.first_name && (
                  <span className="error-text">{errors.first_name}</span>
                )}
              </div>

              <div className="form-group">
                <label>Last Name *</label>
                <input
                  type="text"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleInputChange}
                  className={errors.last_name ? "error" : ""}
                  placeholder="Enter your last name"
                />
                {errors.last_name && (
                  <span className="error-text">{errors.last_name}</span>
                )}
              </div>
            </div>

            <div className="form-group">
              <label>Email Address *</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                className={errors.email ? "error" : ""}
                placeholder="Enter your email address"
              />
              {errors.email && (
                <span className="error-text">{errors.email}</span>
              )}
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Password *</label>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  className={errors.password ? "error" : ""}
                  placeholder="Minimum 8 characters"
                />
                {errors.password && (
                  <span className="error-text">{errors.password}</span>
                )}
              </div>

              <div className="form-group">
                <label>Confirm Password *</label>
                <input
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  className={errors.confirmPassword ? "error" : ""}
                  placeholder="Re-enter your password"
                />
                {errors.confirmPassword && (
                  <span className="error-text">{errors.confirmPassword}</span>
                )}
              </div>
            </div>

            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="terms_agreement"
                  checked={formData.terms_agreement}
                  onChange={handleInputChange}
                />
                I agree to the <a href="/terms" target="_blank">
                  Terms & Conditions
                </a> and <a href="/privacy" target="_blank">
                  Privacy Policy
                </a> *
              </label>
              {errors.terms_agreement && (
                <span className="error-text">{errors.terms_agreement}</span>
              )}
            </div>

            <button
              type="button"
              onClick={handleNextStep}
              className="btn-primary"
            >
              Continue to Payment Details →
            </button>
          </div>
        )}

        {step === 2 && (
          <div className="step-2">
            <h3>Payment & Banking Information</h3>
            <p className="info-text">
              This information is required for secure transactions and will be
              verified by our admin team.
            </p>

            <div className="form-group">
              <label>Phone Number</label>
              <input
                type="tel"
                name="phone_number"
                value={formData.phone_number}
                onChange={handleInputChange}
                placeholder="Enter your phone number"
              />
            </div>

            <div className="form-group">
              <label>UPI ID</label>
              <input
                type="text"
                name="upi_id"
                value={formData.upi_id}
                onChange={handleInputChange}
                placeholder="yourname@paytm or yourname@googleplay"
              />
              <small>For quick payments and settlements</small>
            </div>

            <div className="form-group">
              <label>Bank Account Number</label>
              <input
                type="text"
                name="bank_account"
                value={formData.bank_account}
                onChange={handleInputChange}
                className={errors.bank_account ? "error" : ""}
                placeholder="Enter your bank account number"
              />
              {errors.bank_account && (
                <span className="error-text">{errors.bank_account}</span>
              )}
            </div>

            <div className="form-group">
              <label>IFSC Code</label>
              <input
                type="text"
                name="ifsc_code"
                value={formData.ifsc_code}
                onChange={handleInputChange}
                className={errors.ifsc_code ? "error" : ""}
                placeholder="HDFC0001234"
                maxLength="11"
              />
              {errors.ifsc_code && (
                <span className="error-text">{errors.ifsc_code}</span>
              )}
              <small>11-character bank identifier code</small>
            </div>

            {errors.submit && (
              <div className="error-message">{errors.submit}</div>
            )}

            <div className="form-actions">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="btn-secondary"
              >
                ← Back
              </button>
              <button type="submit" disabled={loading} className="btn-primary">
                {loading ? "Creating Account..." : "Create Account 🚀"}
              </button>
            </div>
          </div>
        )}
      </form>

      <div className="auth-footer">
        Already have an account? <a href="/login">Sign in here</a>
      </div>
    </div>
  );
};

export default RegisterForm;
```

### 2. Registration API Implementation

```javascript
// services/authService.js (Registration methods)
export class AuthService {
  // ... previous code ...

  async register(userData) {
    try {
      const response = await httpClient.post(`${this.baseURL}/register`, {
        first_name: userData.first_name,
        last_name: userData.last_name,
        email: userData.email,
        password: userData.password,
        role: userData.role,
        terms_agreement: userData.terms_agreement,
        phone_number: userData.phone_number || null,
        upi_id: userData.upi_id || null,
        bank_account: userData.bank_account || null,
        ifsc_code: userData.ifsc_code || null,
      });

      return response.data;
    } catch (error) {
      console.error("Registration error:", error);
      throw error;
    }
  }

  async verifyEmail(email, otp) {
    try {
      const response = await httpClient.post(`${this.baseURL}/verify-email`, {
        email,
        otp: parseInt(otp),
      });

      return response.data;
    } catch (error) {
      console.error("Email verification error:", error);
      throw error;
    }
  }

  async resendVerificationEmail(email) {
    try {
      const response = await httpClient.post(
        `${this.baseURL}/resend-verification-email`,
        {
          email,
        }
      );

      return response.data;
    } catch (error) {
      console.error("Resend verification error:", error);
      throw error;
    }
  }
}
```

---

## 🔑 Login Implementation

### 1. Login Form Component

```jsx
// components/auth/LoginForm.jsx
import React, { useState, useContext } from "react";
import { AuthContext } from "../../context/AuthContext";
import { authService } from "../../services/authService";

const LoginForm = () => {
  const { login } = useContext(AuthContext);
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    rememberMe: false,
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));

    // Clear error when user starts typing
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: "" }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.email) {
      newErrors.email = "Email is required";
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = "Email is invalid";
    }

    if (!formData.password) {
      newErrors.password = "Password is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) return;

    setLoading(true);
    try {
      const response = await authService.login(
        formData.email,
        formData.password
      );

      // Save user and tokens
      authService.setTokens(response.data.tokens);
      localStorage.setItem("user", JSON.stringify(response.data.user));

      // Update auth context
      await login(response.data.user);

      // Redirect based on role
      redirectAfterLogin(response.data.user.role);
    } catch (error) {
      setErrors({
        submit:
          error.response?.data?.detail ||
          "Login failed. Please check your credentials.",
      });
    } finally {
      setLoading(false);
    }
  };

  const redirectAfterLogin = (role) => {
    const redirectMap = {
      FARMER: "/farmer/dashboard",
      TRADER: "/trader/dashboard",
      ADMIN: "/admin/dashboard",
    };

    const redirectUrl = redirectMap[role] || "/dashboard";
    window.location.href = redirectUrl;
  };

  return (
    <div className="login-form">
      <div className="login-header">
        <h2>Welcome Back</h2>
        <p>Sign in to your AgriTech account</p>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Email Address</label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleInputChange}
            className={errors.email ? "error" : ""}
            placeholder="Enter your email"
            autoComplete="email"
          />
          {errors.email && <span className="error-text">{errors.email}</span>}
        </div>

        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleInputChange}
            className={errors.password ? "error" : ""}
            placeholder="Enter your password"
            autoComplete="current-password"
          />
          {errors.password && (
            <span className="error-text">{errors.password}</span>
          )}
        </div>

        <div className="form-options">
          <label className="checkbox-label">
            <input
              type="checkbox"
              name="rememberMe"
              checked={formData.rememberMe}
              onChange={handleInputChange}
            />
            Remember me
          </label>

          <a href="/forgot-password" className="forgot-link">
            Forgot password?
          </a>
        </div>

        {errors.submit && <div className="error-message">{errors.submit}</div>}

        <button type="submit" disabled={loading} className="btn-login">
          {loading ? "Signing in..." : "Sign In"}
        </button>

        <div className="social-login">
          <div className="divider">
            <span>Or continue with</span>
          </div>

          {/* Add social login buttons if needed */}
          <div className="social-buttons">
            <button type="button" className="btn-social google">
              <i className="fab fa-google"></i>
              Google
            </button>
          </div>
        </div>
      </form>

      <div className="auth-footer">
        Don't have an account? <a href="/register">Create one here</a>
      </div>
    </div>
  );
};

export default LoginForm;
```

### 2. Login API Implementation

```javascript
// services/authService.js (Login methods)
export class AuthService {
  // ... previous code ...

  async login(email, password) {
    try {
      const response = await httpClient.post(`${this.baseURL}/login`, {
        email,
        password,
      });

      return response.data;
    } catch (error) {
      console.error("Login error:", error);
      throw error;
    }
  }

  async logout() {
    try {
      // Call logout endpoint
      await httpClient.get(`${this.baseURL}/logout`);
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      // Clear local storage regardless
      this.clearTokens();
    }
  }

  async refreshTokens() {
    try {
      const refreshToken = this.getRefreshToken();
      if (!refreshToken) throw new Error("No refresh token");

      const response = await httpClient.post(`${this.baseURL}/refresh`, {
        refresh: refreshToken,
      });

      this.setTokens(response.data.data);
      return true;
    } catch (error) {
      console.error("Token refresh error:", error);
      this.clearTokens();
      return false;
    }
  }

  async getCurrentUserProfile() {
    try {
      const response = await httpClient.get(`${this.baseURL}/me`);
      return response.data.data;
    } catch (error) {
      console.error("Get profile error:", error);
      throw error;
    }
  }
}
```

This is Part 1 of the frontend documentation. Should I continue with the remaining parts covering role-based dashboards, utilities, and API integrations?
