# 🌾 AgriTech Platform - Frontend Integration Guide (Part 2)

## Role-Based Dashboard Implementation & Access Control

---

## 🛡️ Role-Based Access Control

### 1. Permission System

```javascript
// utils/permissions.js
export const ROLES = {
  FARMER: "FARMER",
  TRADER: "TRADER",
  ADMIN: "ADMIN",
};

export const PERMISSIONS = {
  // Commodity Management
  CREATE_LISTING: "create_listing",
  VIEW_LISTINGS: "view_listings",
  EDIT_OWN_LISTING: "edit_own_listing",
  DELETE_OWN_LISTING: "delete_own_listing",

  // Bidding System
  PLACE_BID: "place_bid",
  VIEW_BIDS: "view_bids",
  MANAGE_BIDS: "manage_bids",

  // User Management
  VIEW_USERS: "view_users",
  MANAGE_USERS: "manage_users",
  VERIFY_KYC: "verify_kyc",

  // Admin Functions
  APPROVE_LISTINGS: "approve_listings",
  VIEW_ANALYTICS: "view_analytics",
  MANAGE_PLATFORM: "manage_platform",

  // Price Tracking
  VIEW_PRICE_HISTORY: "view_price_history",
  SET_PRICE_ALERTS: "set_price_alerts",

  // ML Features
  ACCESS_ML_RECOMMENDATIONS: "access_ml_recommendations",
  VIEW_MARKET_INSIGHTS: "view_market_insights",
};

// Role-Permission Mapping
export const ROLE_PERMISSIONS = {
  [ROLES.FARMER]: [
    PERMISSIONS.CREATE_LISTING,
    PERMISSIONS.VIEW_LISTINGS,
    PERMISSIONS.EDIT_OWN_LISTING,
    PERMISSIONS.DELETE_OWN_LISTING,
    PERMISSIONS.VIEW_BIDS,
    PERMISSIONS.VIEW_PRICE_HISTORY,
    PERMISSIONS.SET_PRICE_ALERTS,
    PERMISSIONS.ACCESS_ML_RECOMMENDATIONS,
    PERMISSIONS.VIEW_MARKET_INSIGHTS,
  ],

  [ROLES.TRADER]: [
    PERMISSIONS.VIEW_LISTINGS,
    PERMISSIONS.PLACE_BID,
    PERMISSIONS.VIEW_BIDS,
    PERMISSIONS.MANAGE_BIDS,
    PERMISSIONS.VIEW_PRICE_HISTORY,
    PERMISSIONS.SET_PRICE_ALERTS,
    PERMISSIONS.ACCESS_ML_RECOMMENDATIONS,
    PERMISSIONS.VIEW_MARKET_INSIGHTS,
  ],

  [ROLES.ADMIN]: [
    // Admin has all permissions
    ...Object.values(PERMISSIONS),
  ],
};

// Permission checker functions
export const hasPermission = (userRole, permission) => {
  const rolePermissions = ROLE_PERMISSIONS[userRole] || [];
  return rolePermissions.includes(permission);
};

export const canAccessRoute = (userRole, routePermissions) => {
  if (!routePermissions || routePermissions.length === 0) return true;
  return routePermissions.some((permission) =>
    hasPermission(userRole, permission)
  );
};
```

### 2. Route Protection Component

```jsx
// components/auth/ProtectedRoute.jsx
import React, { useContext } from "react";
import { AuthContext } from "../../context/AuthContext";
import { canAccessRoute } from "../../utils/permissions";

const ProtectedRoute = ({
  children,
  requiredPermissions = [],
  requiredRoles = [],
  fallback = null,
}) => {
  const { user, loading } = useContext(AuthContext);

  if (loading) {
    return <div className="loading-spinner">Loading...</div>;
  }

  if (!user) {
    return (
      <div className="auth-required">Please log in to access this page.</div>
    );
  }

  // Check role-based access
  if (requiredRoles.length > 0 && !requiredRoles.includes(user.role)) {
    return (
      fallback || (
        <div className="access-denied">
          Access denied. Insufficient permissions.
        </div>
      )
    );
  }

  // Check permission-based access
  if (
    requiredPermissions.length > 0 &&
    !canAccessRoute(user.role, requiredPermissions)
  ) {
    return (
      fallback || (
        <div className="access-denied">
          Access denied. Required permissions not found.
        </div>
      )
    );
  }

  return children;
};

export default ProtectedRoute;
```

### 3. Auth Context Provider

```jsx
// context/AuthContext.jsx
import React, { createContext, useState, useEffect } from "react";
import { authService } from "../services/authService";

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    try {
      if (authService.isAuthenticated()) {
        const savedUser = authService.getCurrentUser();
        if (savedUser) {
          setUser(savedUser);
          // Optionally fetch fresh user data
          await refreshUserProfile();
        }
      }
    } catch (error) {
      console.error("Auth initialization error:", error);
      authService.clearTokens();
    } finally {
      setLoading(false);
    }
  };

  const login = async (userData) => {
    setUser(userData);
    localStorage.setItem("user", JSON.stringify(userData));
  };

  const logout = async () => {
    await authService.logout();
    setUser(null);
  };

  const refreshUserProfile = async () => {
    try {
      const profile = await authService.getCurrentUserProfile();
      setUser(profile);
      localStorage.setItem("user", JSON.stringify(profile));
    } catch (error) {
      console.error("Profile refresh error:", error);
    }
  };

  const value = {
    user,
    loading,
    login,
    logout,
    refreshUserProfile,
    isAuthenticated: () => !!user,
    hasRole: (role) => user?.role === role,
    hasAnyRole: (roles) => roles.includes(user?.role),
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
```

---

## 📊 Dashboard Components

### 1. Main Dashboard Router

```jsx
// components/dashboard/DashboardRouter.jsx
import React, { useContext } from "react";
import { AuthContext } from "../../context/AuthContext";
import FarmerDashboard from "./FarmerDashboard";
import TraderDashboard from "./TraderDashboard";
import AdminDashboard from "./AdminDashboard";
import { ROLES } from "../../utils/permissions";

const DashboardRouter = () => {
  const { user } = useContext(AuthContext);

  if (!user) {
    return <div>Please log in to access dashboard</div>;
  }

  const dashboardComponents = {
    [ROLES.FARMER]: FarmerDashboard,
    [ROLES.TRADER]: TraderDashboard,
    [ROLES.ADMIN]: AdminDashboard,
  };

  const DashboardComponent = dashboardComponents[user.role];

  if (!DashboardComponent) {
    return <div>Invalid user role</div>;
  }

  return <DashboardComponent user={user} />;
};

export default DashboardRouter;
```

### 2. Farmer Dashboard

```jsx
// components/dashboard/FarmerDashboard.jsx
import React, { useState, useEffect } from "react";
import { farmerService } from "../../services/farmerService";
import { commodityService } from "../../services/commodityService";
import { mlService } from "../../services/mlService";

const FarmerDashboard = ({ user }) => {
  const [stats, setStats] = useState({});
  const [listings, setListings] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);

      // Load in parallel for better performance
      const [farmerStats, myListings, mlRecommendations] = await Promise.all([
        farmerService.getProfile(),
        commodityService.getMyListings(),
        mlService.getRecommendations(user.id),
      ]);

      setStats(farmerStats.data);
      setListings(myListings.data);
      setRecommendations(mlRecommendations.data);
    } catch (error) {
      console.error("Dashboard load error:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="dashboard-loading">Loading dashboard...</div>;
  }

  return (
    <div className="farmer-dashboard">
      {/* Dashboard Header */}
      <div className="dashboard-header">
        <div className="welcome-section">
          <h1>Welcome back, {user.first_name}! 🌾</h1>
          <p>Manage your agricultural listings and track market trends</p>
        </div>

        <div className="quick-actions">
          <button
            className="btn-primary"
            onClick={() => (window.location.href = "/farmer/create-listing")}
          >
            + Create New Listing
          </button>
          <button
            className="btn-secondary"
            onClick={() => (window.location.href = "/farmer/analytics")}
          >
            📊 View Analytics
          </button>
        </div>
      </div>

      {/* KYC Status Banner */}
      {!user.is_verified && (
        <div className="kyc-banner warning">
          <div className="banner-content">
            <strong>⚠️ KYC Verification Pending</strong>
            <p>
              Your account is under review. You'll be able to receive payments
              once verified.
            </p>
            <button className="btn-link">Contact Support</button>
          </div>
        </div>
      )}

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📦</div>
          <div className="stat-content">
            <h3>{stats.total_listings || 0}</h3>
            <p>Total Listings</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">✅</div>
          <div className="stat-content">
            <h3>{stats.active_listings || 0}</h3>
            <p>Active Listings</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">💰</div>
          <div className="stat-content">
            <h3>₹{stats.total_revenue || 0}</h3>
            <p>Total Revenue</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📈</div>
          <div className="stat-content">
            <h3>{stats.successful_sales || 0}</h3>
            <p>Successful Sales</p>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="dashboard-grid">
        {/* Recent Listings */}
        <div className="dashboard-section">
          <div className="section-header">
            <h2>Recent Listings</h2>
            <a href="/farmer/listings" className="view-all">
              View All
            </a>
          </div>

          <div className="listings-list">
            {listings.slice(0, 5).map((listing) => (
              <div key={listing.id} className="listing-item">
                <div className="listing-image">
                  <img
                    src={listing.image_url || "/default-crop.jpg"}
                    alt={listing.name}
                  />
                </div>
                <div className="listing-details">
                  <h4>{listing.name}</h4>
                  <p className="listing-price">₹{listing.current_price}/kg</p>
                  <span className={`status ${listing.status}`}>
                    {listing.status}
                  </span>
                </div>
                <div className="listing-actions">
                  <button
                    onClick={() =>
                      (window.location.href = `/farmer/listings/${listing.id}/edit`)
                    }
                  >
                    Edit
                  </button>
                  <button
                    onClick={() =>
                      (window.location.href = `/listings/${listing.id}`)
                    }
                  >
                    View
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ML Recommendations */}
        <div className="dashboard-section">
          <div className="section-header">
            <h2>🤖 AI Recommendations</h2>
            <span className="beta-badge">Beta</span>
          </div>

          <div className="recommendations-list">
            {recommendations.slice(0, 3).map((rec) => (
              <div key={rec.id} className="recommendation-item">
                <div className={`rec-type ${rec.type}`}>
                  {rec.type === "PRICE"
                    ? "💰"
                    : rec.type === "TIMING"
                    ? "⏰"
                    : "📊"}
                </div>
                <div className="rec-content">
                  <h4>{rec.title}</h4>
                  <p>{rec.description}</p>
                  <small>
                    Confidence: {(rec.confidence * 100).toFixed(0)}%
                  </small>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Market Trends */}
        <div className="dashboard-section full-width">
          <div className="section-header">
            <h2>📈 Market Trends</h2>
            <select onChange={(e) => loadTrends(e.target.value)}>
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
              <option value="90">Last 3 months</option>
            </select>
          </div>

          <div className="trends-chart">
            {/* Integrate chart library here */}
            <div className="chart-placeholder">
              <p>Price trends chart will be displayed here</p>
              <button
                onClick={() => (window.location.href = "/farmer/analytics")}
              >
                View Detailed Analytics
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions Footer */}
      <div className="dashboard-footer">
        <div className="quick-links">
          <a href="/farmer/profile">Profile Settings</a>
          <a href="/farmer/payments">Payment History</a>
          <a href="/farmer/support">Get Support</a>
          <a href="/farmer/help">Help Center</a>
        </div>
      </div>
    </div>
  );
};

export default FarmerDashboard;
```

### 3. Trader Dashboard

```jsx
// components/dashboard/TraderDashboard.jsx
import React, { useState, useEffect } from "react";
import { traderService } from "../../services/traderService";
import { biddingService } from "../../services/biddingService";
import { watchlistService } from "../../services/watchlistService";

const TraderDashboard = ({ user }) => {
  const [stats, setStats] = useState({});
  const [activeBids, setActiveBids] = useState([]);
  const [watchlist, setWatchlist] = useState([]);
  const [marketInsights, setMarketInsights] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);

      const [traderStats, myBids, myWatchlist, insights] = await Promise.all([
        traderService.getProfile(),
        biddingService.getMyBids(),
        watchlistService.getWatchlist(),
        mlService.getMarketInsights(),
      ]);

      setStats(traderStats.data);
      setActiveBids(myBids.data);
      setWatchlist(myWatchlist.data);
      setMarketInsights(insights.data);
    } catch (error) {
      console.error("Dashboard load error:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="dashboard-loading">Loading dashboard...</div>;
  }

  return (
    <div className="trader-dashboard">
      {/* Dashboard Header */}
      <div className="dashboard-header">
        <div className="welcome-section">
          <h1>Welcome back, {user.first_name}! 🏪</h1>
          <p>Discover opportunities and manage your bidding activities</p>
        </div>

        <div className="quick-actions">
          <button
            className="btn-primary"
            onClick={() => (window.location.href = "/commodities")}
          >
            🔍 Browse Commodities
          </button>
          <button
            className="btn-secondary"
            onClick={() => (window.location.href = "/trader/watchlist")}
          >
            ⭐ My Watchlist
          </button>
        </div>
      </div>

      {/* KYC Status Banner */}
      {!user.is_verified && (
        <div className="kyc-banner warning">
          <div className="banner-content">
            <strong>⚠️ KYC Verification Required</strong>
            <p>Complete KYC verification to start bidding on commodities.</p>
            <button className="btn-link">Complete KYC</button>
          </div>
        </div>
      )}

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">💰</div>
          <div className="stat-content">
            <h3>{stats.active_bids || 0}</h3>
            <p>Active Bids</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">✅</div>
          <div className="stat-content">
            <h3>{stats.won_bids || 0}</h3>
            <p>Won Bids</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📊</div>
          <div className="stat-content">
            <h3>₹{stats.total_spent || 0}</h3>
            <p>Total Spent</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">⭐</div>
          <div className="stat-content">
            <h3>{stats.watchlist_items || 0}</h3>
            <p>Watchlist Items</p>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="dashboard-grid">
        {/* Active Bids */}
        <div className="dashboard-section">
          <div className="section-header">
            <h2>Active Bids</h2>
            <a href="/trader/bids" className="view-all">
              View All
            </a>
          </div>

          <div className="bids-list">
            {activeBids.slice(0, 5).map((bid) => (
              <div key={bid.id} className="bid-item">
                <div className="bid-commodity">
                  <img src={bid.commodity.image_url} alt={bid.commodity.name} />
                  <div>
                    <h4>{bid.commodity.name}</h4>
                    <p>{bid.commodity.category}</p>
                  </div>
                </div>
                <div className="bid-details">
                  <p className="bid-amount">₹{bid.amount}</p>
                  <span className={`bid-status ${bid.status}`}>
                    {bid.status}
                  </span>
                  <small>
                    Placed {new Date(bid.created_at).toLocaleDateString()}
                  </small>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Watchlist */}
        <div className="dashboard-section">
          <div className="section-header">
            <h2>⭐ Watchlist</h2>
            <a href="/trader/watchlist" className="view-all">
              Manage
            </a>
          </div>

          <div className="watchlist-items">
            {watchlist.slice(0, 4).map((item) => (
              <div key={item.id} className="watchlist-item">
                <img src={item.commodity.image_url} alt={item.commodity.name} />
                <div className="item-details">
                  <h4>{item.commodity.name}</h4>
                  <p className="price">₹{item.commodity.current_price}/kg</p>
                  <button
                    className="btn-small"
                    onClick={() =>
                      (window.location.href = `/commodities/${item.commodity.id}`)
                    }
                  >
                    View Details
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Market Insights */}
        <div className="dashboard-section full-width">
          <div className="section-header">
            <h2>🔮 Market Insights</h2>
            <span className="ai-badge">AI Powered</span>
          </div>

          <div className="insights-grid">
            {marketInsights.map((insight) => (
              <div key={insight.id} className="insight-card">
                <div className="insight-header">
                  <span className={`insight-type ${insight.type}`}>
                    {insight.type === "BUY"
                      ? "📈"
                      : insight.type === "SELL"
                      ? "📉"
                      : "⚡"}
                  </span>
                  <h4>{insight.commodity_name}</h4>
                </div>
                <p className="insight-text">{insight.description}</p>
                <div className="insight-footer">
                  <span className="confidence">
                    Confidence: {(insight.confidence * 100).toFixed(0)}%
                  </span>
                  <button className="btn-link">Learn More</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TraderDashboard;
```

This is Part 2 of the guide. Should I continue with Part 3 covering the Admin Dashboard and service implementations?
