# 🌾 AgriTech Platform - Frontend Integration Guide (Part 4)

## ML Services, Utilities & Implementation Examples

---

## 🤖 ML Services Integration

### 1. ML Recommendations Service

```javascript
// services/mlService.js
import BaseService from "./baseService";

class MLService extends BaseService {
  constructor() {
    super("/ml");
  }

  // Personal Recommendations
  async getRecommendations(userId, params = {}) {
    return this.get("/recommendations", { user_id: userId, ...params });
  }

  async getUserRecommendations(filters = {}) {
    return this.get("/recommendations/user", filters);
  }

  async getCommodityRecommendations(commodityId) {
    return this.get(`/recommendations/commodity/${commodityId}`);
  }

  // Market Insights
  async getMarketInsights() {
    return this.get("/insights/market");
  }

  async getMarketOverview() {
    return this.get("/insights/overview");
  }

  async getPriceAnalysis(commodityId, timeframe = "30") {
    return this.get(`/insights/price/${commodityId}`, { days: timeframe });
  }

  // Trading Suggestions
  async getTradingOpportunities(userRole = "TRADER") {
    return this.get("/trading/opportunities", { role: userRole });
  }

  async getBidRecommendations(commodityId) {
    return this.get(`/trading/bid-recommendations/${commodityId}`);
  }

  async getOptimalPricing(commodityData) {
    return this.post("/pricing/optimize", commodityData);
  }

  // Demand Forecasting
  async getDemandForecast(commodityCategory, region = null) {
    return this.get("/forecast/demand", {
      category: commodityCategory,
      region: region,
    });
  }

  async getSeasonalTrends(commodityType) {
    return this.get(`/trends/seasonal/${commodityType}`);
  }

  // Risk Assessment
  async getRiskAssessment(portfolioData) {
    return this.post("/risk/assess", portfolioData);
  }

  async getMarketVolatility(timeframe = "30") {
    return this.get("/risk/volatility", { days: timeframe });
  }
}

export const mlService = new MLService();
```

### 2. Price Tracking Service

```javascript
// services/priceTrackingService.js
import BaseService from "./baseService";

class PriceTrackingService extends BaseService {
  constructor() {
    super("/price-tracking");
  }

  // Price History
  async getPriceHistory(commodityId, timeframe = "30") {
    return this.get(`/history/${commodityId}`, { days: timeframe });
  }

  async getAveragePrices(category, timeframe = "30") {
    return this.get("/average", { category, days: timeframe });
  }

  async getCurrentMarketPrices() {
    return this.get("/current");
  }

  // Price Alerts
  async getMyAlerts() {
    return this.get("/alerts");
  }

  async createAlert(alertData) {
    return this.post("/alerts", {
      commodity_id: alertData.commodityId,
      alert_type: alertData.type, // 'PRICE_DROP', 'PRICE_RISE', 'TARGET_PRICE'
      threshold_value: alertData.threshold,
      notification_channels: alertData.channels, // ['EMAIL', 'SMS', 'PUSH']
    });
  }

  async updateAlert(alertId, alertData) {
    return this.put(`/alerts/${alertId}`, alertData);
  }

  async deleteAlert(alertId) {
    return this.delete(`/alerts/${alertId}`);
  }

  // Market Trends
  async getTrendAnalysis(commodityId) {
    return this.get(`/trends/${commodityId}`);
  }

  async getMarketComparison(commodityIds) {
    return this.post("/compare", { commodity_ids: commodityIds });
  }

  async getRegionalPrices(commodityId, regions = []) {
    return this.get(`/regional/${commodityId}`, { regions });
  }
}

export const priceTrackingService = new PriceTrackingService();
```

---

## 🔧 Utility Functions

### 1. Format Utilities

```javascript
// utils/formatters.js

// Currency formatting
export const formatCurrency = (amount, currency = "INR") => {
  if (amount === null || amount === undefined) return "₹0";

  const formatter = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  });

  return formatter.format(amount);
};

// Compact currency (1K, 1M, etc.)
export const formatCompactCurrency = (amount) => {
  if (amount >= 10000000) {
    // 1 Crore
    return `₹${(amount / 10000000).toFixed(1)}Cr`;
  } else if (amount >= 100000) {
    // 1 Lakh
    return `₹${(amount / 100000).toFixed(1)}L`;
  } else if (amount >= 1000) {
    // 1 Thousand
    return `₹${(amount / 1000).toFixed(1)}K`;
  }
  return `₹${amount}`;
};

// Date formatting
export const formatDate = (dateString, format = "short") => {
  const date = new Date(dateString);

  const formats = {
    short: { day: "numeric", month: "short", year: "numeric" },
    long: { day: "numeric", month: "long", year: "numeric" },
    time: { hour: "2-digit", minute: "2-digit" },
    datetime: {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    },
  };

  return date.toLocaleDateString("en-IN", formats[format]);
};

// Time ago formatting
export const formatTimeAgo = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now - date) / 1000);

  if (diffInSeconds < 60) return "Just now";
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
  if (diffInSeconds < 2592000)
    return `${Math.floor(diffInSeconds / 86400)}d ago`;

  return formatDate(dateString);
};

// Number formatting
export const formatNumber = (number, decimals = 0) => {
  return new Intl.NumberFormat("en-IN", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(number);
};

// Percentage formatting
export const formatPercentage = (value, decimals = 1) => {
  return `${value.toFixed(decimals)}%`;
};

// File size formatting
export const formatFileSize = (bytes) => {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

// Status formatting
export const formatStatus = (status) => {
  const statusMap = {
    active: "Active",
    inactive: "Inactive",
    pending: "Pending Approval",
    approved: "Approved",
    rejected: "Rejected",
    completed: "Completed",
    cancelled: "Cancelled",
  };

  return statusMap[status.toLowerCase()] || status;
};
```

### 2. Validation Utilities

```javascript
// utils/validators.js

// Email validation
export const isValidEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

// Password validation
export const validatePassword = (password) => {
  const errors = [];

  if (password.length < 8) {
    errors.push("Password must be at least 8 characters long");
  }

  if (!/[A-Z]/.test(password)) {
    errors.push("Password must contain at least one uppercase letter");
  }

  if (!/[a-z]/.test(password)) {
    errors.push("Password must contain at least one lowercase letter");
  }

  if (!/\d/.test(password)) {
    errors.push("Password must contain at least one number");
  }

  if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
    errors.push("Password must contain at least one special character");
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
};

// Phone number validation
export const isValidPhoneNumber = (phone) => {
  const phoneRegex = /^[6-9]\d{9}$/;
  return phoneRegex.test(phone.replace(/\s+/g, ""));
};

// IFSC code validation
export const isValidIFSC = (ifsc) => {
  const ifscRegex = /^[A-Z]{4}0[A-Z0-9]{6}$/;
  return ifscRegex.test(ifsc.toUpperCase());
};

// Bank account validation
export const isValidBankAccount = (account) => {
  return /^\d{9,18}$/.test(account);
};

// UPI ID validation
export const isValidUPI = (upi) => {
  const upiRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+$/;
  return upiRegex.test(upi);
};

// Form validation helper
export const validateForm = (formData, rules) => {
  const errors = {};

  Object.keys(rules).forEach((field) => {
    const value = formData[field];
    const fieldRules = rules[field];

    // Required validation
    if (fieldRules.required && (!value || value.toString().trim() === "")) {
      errors[field] = `${fieldRules.label || field} is required`;
      return;
    }

    // Skip other validations if field is empty and not required
    if (!value && !fieldRules.required) return;

    // Min length validation
    if (fieldRules.minLength && value.length < fieldRules.minLength) {
      errors[field] = `${fieldRules.label || field} must be at least ${
        fieldRules.minLength
      } characters`;
      return;
    }

    // Max length validation
    if (fieldRules.maxLength && value.length > fieldRules.maxLength) {
      errors[field] = `${fieldRules.label || field} must not exceed ${
        fieldRules.maxLength
      } characters`;
      return;
    }

    // Custom validation
    if (fieldRules.validator) {
      const validationResult = fieldRules.validator(value);
      if (validationResult !== true) {
        errors[field] = validationResult;
        return;
      }
    }

    // Type-specific validation
    if (fieldRules.type === "email" && !isValidEmail(value)) {
      errors[field] = "Please enter a valid email address";
    } else if (fieldRules.type === "phone" && !isValidPhoneNumber(value)) {
      errors[field] = "Please enter a valid phone number";
    } else if (fieldRules.type === "ifsc" && !isValidIFSC(value)) {
      errors[field] = "Please enter a valid IFSC code";
    }
  });

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
};
```

### 3. Local Storage Utilities

```javascript
// utils/storage.js

class StorageManager {
  // Set item with expiration
  setItem(key, value, expirationHours = null) {
    const item = {
      value: value,
      timestamp: Date.now(),
      expiration: expirationHours
        ? Date.now() + expirationHours * 60 * 60 * 1000
        : null,
    };

    try {
      localStorage.setItem(key, JSON.stringify(item));
    } catch (error) {
      console.error("Error saving to localStorage:", error);
    }
  }

  // Get item with expiration check
  getItem(key) {
    try {
      const itemStr = localStorage.getItem(key);
      if (!itemStr) return null;

      const item = JSON.parse(itemStr);

      // Check expiration
      if (item.expiration && Date.now() > item.expiration) {
        this.removeItem(key);
        return null;
      }

      return item.value;
    } catch (error) {
      console.error("Error reading from localStorage:", error);
      return null;
    }
  }

  // Remove item
  removeItem(key) {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error("Error removing from localStorage:", error);
    }
  }

  // Clear all items
  clear() {
    try {
      localStorage.clear();
    } catch (error) {
      console.error("Error clearing localStorage:", error);
    }
  }

  // Check if item exists and is not expired
  hasItem(key) {
    return this.getItem(key) !== null;
  }

  // Get all keys
  getAllKeys() {
    try {
      return Object.keys(localStorage);
    } catch (error) {
      console.error("Error getting localStorage keys:", error);
      return [];
    }
  }
}

export const storage = new StorageManager();

// Specific storage helpers
export const authStorage = {
  setTokens: (tokens) => {
    storage.setItem("access_token", tokens.access_token, 24); // 24 hours
    storage.setItem("refresh_token", tokens.refresh_token, 24 * 7); // 7 days
  },

  getTokens: () => ({
    access_token: storage.getItem("access_token"),
    refresh_token: storage.getItem("refresh_token"),
  }),

  clearTokens: () => {
    storage.removeItem("access_token");
    storage.removeItem("refresh_token");
  },

  setUser: (user) => {
    storage.setItem("user", user, 24); // 24 hours
  },

  getUser: () => storage.getItem("user"),

  clearUser: () => storage.removeItem("user"),
};
```

---

## 📱 State Management

### 1. React Context for Global State

```jsx
// context/AppContext.jsx
import React, { createContext, useContext, useReducer } from "react";

// Action types
const ActionTypes = {
  SET_LOADING: "SET_LOADING",
  SET_ERROR: "SET_ERROR",
  CLEAR_ERROR: "CLEAR_ERROR",
  SET_NOTIFICATIONS: "SET_NOTIFICATIONS",
  ADD_NOTIFICATION: "ADD_NOTIFICATION",
  REMOVE_NOTIFICATION: "REMOVE_NOTIFICATION",
  SET_THEME: "SET_THEME",
  SET_LANGUAGE: "SET_LANGUAGE",
};

// Initial state
const initialState = {
  loading: false,
  error: null,
  notifications: [],
  theme: "light",
  language: "en",
  socketConnected: false,
};

// Reducer
const appReducer = (state, action) => {
  switch (action.type) {
    case ActionTypes.SET_LOADING:
      return { ...state, loading: action.payload };

    case ActionTypes.SET_ERROR:
      return { ...state, error: action.payload };

    case ActionTypes.CLEAR_ERROR:
      return { ...state, error: null };

    case ActionTypes.SET_NOTIFICATIONS:
      return { ...state, notifications: action.payload };

    case ActionTypes.ADD_NOTIFICATION:
      return {
        ...state,
        notifications: [...state.notifications, action.payload],
      };

    case ActionTypes.REMOVE_NOTIFICATION:
      return {
        ...state,
        notifications: state.notifications.filter(
          (n) => n.id !== action.payload
        ),
      };

    case ActionTypes.SET_THEME:
      return { ...state, theme: action.payload };

    case ActionTypes.SET_LANGUAGE:
      return { ...state, language: action.payload };

    default:
      return state;
  }
};

// Context
const AppContext = createContext();

// Provider component
export const AppProvider = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Actions
  const setLoading = (loading) => {
    dispatch({ type: ActionTypes.SET_LOADING, payload: loading });
  };

  const setError = (error) => {
    dispatch({ type: ActionTypes.SET_ERROR, payload: error });
  };

  const clearError = () => {
    dispatch({ type: ActionTypes.CLEAR_ERROR });
  };

  const addNotification = (notification) => {
    const id = Date.now().toString();
    dispatch({
      type: ActionTypes.ADD_NOTIFICATION,
      payload: { id, ...notification },
    });

    // Auto remove after 5 seconds
    setTimeout(() => {
      removeNotification(id);
    }, 5000);
  };

  const removeNotification = (id) => {
    dispatch({ type: ActionTypes.REMOVE_NOTIFICATION, payload: id });
  };

  const setTheme = (theme) => {
    dispatch({ type: ActionTypes.SET_THEME, payload: theme });
    localStorage.setItem("theme", theme);
  };

  const value = {
    ...state,
    setLoading,
    setError,
    clearError,
    addNotification,
    removeNotification,
    setTheme,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

// Hook to use app context
export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useApp must be used within AppProvider");
  }
  return context;
};
```

### 2. WebSocket Integration

```javascript
// services/websocketService.js
class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectInterval = 1000;
    this.listeners = new Map();
  }

  connect(userId) {
    try {
      const wsUrl = `ws://localhost:8000/api/v6/realtime/ws/${userId}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log("WebSocket connected");
        this.reconnectAttempts = 0;
        this.emit("connected", true);
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
        }
      };

      this.ws.onclose = () => {
        console.log("WebSocket disconnected");
        this.emit("connected", false);
        this.attemptReconnect(userId);
      };

      this.ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        this.emit("error", error);
      };
    } catch (error) {
      console.error("WebSocket connection error:", error);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  attemptReconnect(userId) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      setTimeout(() => {
        this.reconnectAttempts++;
        console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
        this.connect(userId);
      }, this.reconnectInterval * this.reconnectAttempts);
    }
  }

  handleMessage(data) {
    const { type, payload } = data;

    switch (type) {
      case "bid_update":
        this.emit("bidUpdate", payload);
        break;
      case "new_bid":
        this.emit("newBid", payload);
        break;
      case "auction_ended":
        this.emit("auctionEnded", payload);
        break;
      case "price_alert":
        this.emit("priceAlert", payload);
        break;
      case "notification":
        this.emit("notification", payload);
        break;
      default:
        console.log("Unknown message type:", type);
    }
  }

  // Event listener management
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach((callback) => {
        try {
          callback(data);
        } catch (error) {
          console.error("Error in WebSocket event callback:", error);
        }
      });
    }
  }

  // Send message to server
  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.error("WebSocket is not connected");
    }
  }
}

export const websocketService = new WebSocketService();
```

This completes the comprehensive frontend integration guide. The documentation now covers:

✅ **Complete Authentication System** - Registration, login, token management
✅ **Role-Based Access Control** - Permissions, route protection, middleware
✅ **Dashboard Components** - Farmer, Trader, and Admin dashboards
✅ **Service Layer** - All API integrations with proper error handling
✅ **ML Integration** - Recommendations, insights, price tracking
✅ **Utility Functions** - Formatters, validators, storage management
✅ **State Management** - Context providers, WebSocket integration
✅ **Extensible Architecture** - Open-ended design for future features

The frontend team can now implement a fully functional agricultural trading platform with role-based dashboards and comprehensive API integration!
