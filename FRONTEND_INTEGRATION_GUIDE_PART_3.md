# 🌾 AgriTech Platform - Frontend Integration Guide (Part 3)

## Admin Dashboard & Service Layer Implementation

---

## 👑 Admin Dashboard

### 1. Admin Dashboard Component

```jsx
// components/dashboard/AdminDashboard.jsx
import React, { useState, useEffect } from "react";
import { adminService } from "../../services/adminService";
import { analyticsService } from "../../services/analyticsService";

const AdminDashboard = ({ user }) => {
  const [platformStats, setPlatformStats] = useState({});
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [recentUsers, setRecentUsers] = useState([]);
  const [systemHealth, setSystemHealth] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAdminDashboard();
  }, []);

  const loadAdminDashboard = async () => {
    try {
      setLoading(true);

      const [stats, approvals, users, health] = await Promise.all([
        adminService.getPlatformStats(),
        adminService.getPendingCommodities(),
        adminService.getRecentUsers(),
        adminService.getSystemHealth(),
      ]);

      setPlatformStats(stats.data);
      setPendingApprovals(approvals.data);
      setRecentUsers(users.data);
      setSystemHealth(health.data);
    } catch (error) {
      console.error("Admin dashboard load error:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleApproval = async (commodityId, isApproved) => {
    try {
      await adminService.approveCommodity(commodityId, isApproved);
      // Refresh pending approvals
      const approvals = await adminService.getPendingCommodities();
      setPendingApprovals(approvals.data);
    } catch (error) {
      console.error("Approval error:", error);
    }
  };

  const handleUserVerification = async (userId, isVerified) => {
    try {
      await adminService.updateUserVerification(userId, isVerified);
      // Refresh users list
      const users = await adminService.getRecentUsers();
      setRecentUsers(users.data);
    } catch (error) {
      console.error("User verification error:", error);
    }
  };

  if (loading) {
    return <div className="dashboard-loading">Loading admin dashboard...</div>;
  }

  return (
    <div className="admin-dashboard">
      {/* Dashboard Header */}
      <div className="dashboard-header">
        <div className="welcome-section">
          <h1>Admin Control Panel 👑</h1>
          <p>Manage platform operations and monitor system health</p>
        </div>

        <div className="quick-actions">
          <button
            className="btn-primary"
            onClick={() => (window.location.href = "/admin/users")}
          >
            👥 Manage Users
          </button>
          <button
            className="btn-secondary"
            onClick={() => (window.location.href = "/admin/analytics")}
          >
            📊 View Analytics
          </button>
        </div>
      </div>

      {/* System Health Status */}
      <div className="system-health">
        <h2>🔧 System Health</h2>
        <div className="health-grid">
          <div className={`health-card ${systemHealth.database?.status}`}>
            <div className="health-icon">🗄️</div>
            <div className="health-details">
              <h4>Database</h4>
              <span className="status">{systemHealth.database?.status}</span>
            </div>
          </div>

          <div className={`health-card ${systemHealth.redis?.status}`}>
            <div className="health-icon">⚡</div>
            <div className="health-details">
              <h4>Redis Cache</h4>
              <span className="status">{systemHealth.redis?.status}</span>
            </div>
          </div>

          <div className={`health-card ${systemHealth.api?.status}`}>
            <div className="health-icon">🌐</div>
            <div className="health-details">
              <h4>API Server</h4>
              <span className="status">{systemHealth.api?.status}</span>
            </div>
          </div>

          <div className={`health-card ${systemHealth.ml?.status}`}>
            <div className="health-icon">🤖</div>
            <div className="health-details">
              <h4>ML Services</h4>
              <span className="status">{systemHealth.ml?.status}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Platform Statistics */}
      <div className="platform-stats">
        <h2>📊 Platform Overview</h2>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">👥</div>
            <div className="stat-content">
              <h3>{platformStats.total_users || 0}</h3>
              <p>Total Users</p>
              <small>+{platformStats.new_users_today || 0} today</small>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">📦</div>
            <div className="stat-content">
              <h3>{platformStats.total_commodities || 0}</h3>
              <p>Total Commodities</p>
              <small>{platformStats.active_commodities || 0} active</small>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">💰</div>
            <div className="stat-content">
              <h3>₹{platformStats.total_revenue || 0}</h3>
              <p>Total Revenue</p>
              <small>₹{platformStats.revenue_today || 0} today</small>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">🎯</div>
            <div className="stat-content">
              <h3>{platformStats.total_bids || 0}</h3>
              <p>Total Bids</p>
              <small>{platformStats.active_bids || 0} active</small>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="dashboard-grid">
        {/* Pending Approvals */}
        <div className="dashboard-section">
          <div className="section-header">
            <h2>⏳ Pending Approvals</h2>
            <span className="count-badge">{pendingApprovals.length}</span>
          </div>

          <div className="approvals-list">
            {pendingApprovals.slice(0, 5).map((commodity) => (
              <div key={commodity.id} className="approval-item">
                <div className="commodity-info">
                  <img src={commodity.image_url} alt={commodity.name} />
                  <div>
                    <h4>{commodity.name}</h4>
                    <p>
                      {commodity.category} • {commodity.quantity}kg
                    </p>
                    <small>By: {commodity.farmer_name}</small>
                  </div>
                </div>
                <div className="approval-actions">
                  <button
                    className="btn-approve"
                    onClick={() => handleApproval(commodity.id, true)}
                  >
                    ✅ Approve
                  </button>
                  <button
                    className="btn-reject"
                    onClick={() => handleApproval(commodity.id, false)}
                  >
                    ❌ Reject
                  </button>
                  <button
                    className="btn-details"
                    onClick={() =>
                      (window.location.href = `/admin/commodities/${commodity.id}`)
                    }
                  >
                    📋 Details
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Users */}
        <div className="dashboard-section">
          <div className="section-header">
            <h2>👤 Recent Users</h2>
            <a href="/admin/users" className="view-all">
              View All
            </a>
          </div>

          <div className="users-list">
            {recentUsers.slice(0, 5).map((user) => (
              <div key={user.id} className="user-item">
                <div className="user-info">
                  <div className="user-avatar">
                    <img
                      src={user.avatar_url || "/default-avatar.png"}
                      alt={user.full_name}
                    />
                  </div>
                  <div>
                    <h4>{user.full_name}</h4>
                    <p>{user.email}</p>
                    <span className={`role-badge ${user.role}`}>
                      {user.role}
                    </span>
                  </div>
                </div>
                <div className="user-status">
                  <div
                    className={`verification-status ${
                      user.is_verified ? "verified" : "pending"
                    }`}
                  >
                    {user.is_verified ? "✅ Verified" : "⏳ Pending"}
                  </div>
                  {!user.is_verified && (
                    <button
                      className="btn-verify"
                      onClick={() => handleUserVerification(user.id, true)}
                    >
                      Verify KYC
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Activity Monitor */}
        <div className="dashboard-section full-width">
          <div className="section-header">
            <h2>📈 Real-time Activity</h2>
            <div className="time-filters">
              <button className="active">Live</button>
              <button>1H</button>
              <button>24H</button>
            </div>
          </div>

          <div className="activity-feed">
            <div className="activity-item">
              <span className="activity-time">2 min ago</span>
              <span className="activity-text">
                New user registered: farmer@example.com
              </span>
              <span className="activity-type new-user">New User</span>
            </div>
            <div className="activity-item">
              <span className="activity-time">5 min ago</span>
              <span className="activity-text">
                Commodity approved: Premium Wheat
              </span>
              <span className="activity-type approval">Approval</span>
            </div>
            <div className="activity-item">
              <span className="activity-time">8 min ago</span>
              <span className="activity-text">
                High-value bid placed: ₹50,000
              </span>
              <span className="activity-type bid">Bid</span>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Management Tools */}
      <div className="management-tools">
        <h2>🛠️ Management Tools</h2>
        <div className="tools-grid">
          <div
            className="tool-card"
            onClick={() => (window.location.href = "/admin/bulk-actions")}
          >
            <div className="tool-icon">📋</div>
            <h4>Bulk Actions</h4>
            <p>Perform bulk operations on users and commodities</p>
          </div>

          <div
            className="tool-card"
            onClick={() => (window.location.href = "/admin/reports")}
          >
            <div className="tool-icon">📊</div>
            <h4>Generate Reports</h4>
            <p>Create detailed platform reports</p>
          </div>

          <div
            className="tool-card"
            onClick={() => (window.location.href = "/admin/settings")}
          >
            <div className="tool-icon">⚙️</div>
            <h4>Platform Settings</h4>
            <p>Configure platform parameters</p>
          </div>

          <div
            className="tool-card"
            onClick={() => (window.location.href = "/admin/audit-logs")}
          >
            <div className="tool-icon">🔍</div>
            <h4>Audit Logs</h4>
            <p>View system audit logs</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
```

---

## 🔧 Service Layer Implementation

### 1. Base API Service

```javascript
// services/baseService.js
import axios from "axios";
import { API_CONFIG } from "../config/api";

class BaseService {
  constructor(endpoint) {
    this.endpoint = endpoint;
    this.baseURL = API_CONFIG.BASE_URL + endpoint;
    this.setupAxios();
  }

  setupAxios() {
    // Create axios instance with default config
    this.api = axios.create({
      baseURL: this.baseURL,
      timeout: API_CONFIG.TIMEOUT,
      withCredentials: true,
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
    });

    // Request interceptor
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem("access_token");
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Handle token expiration
          try {
            await this.refreshToken();
            return this.api.request(error.config);
          } catch (refreshError) {
            this.handleAuthError();
            return Promise.reject(refreshError);
          }
        }
        return Promise.reject(error);
      }
    );
  }

  async refreshToken() {
    const refreshToken = localStorage.getItem("refresh_token");
    if (!refreshToken) throw new Error("No refresh token");

    const response = await axios.post(`${API_CONFIG.BASE_URL}/auth/refresh`, {
      refresh: refreshToken,
    });

    const { access_token, refresh_token } = response.data.data;
    localStorage.setItem("access_token", access_token);
    localStorage.setItem("refresh_token", refresh_token);
  }

  handleAuthError() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    window.location.href = "/login";
  }

  // Common HTTP methods
  async get(url, params = {}) {
    const response = await this.api.get(url, { params });
    return response.data;
  }

  async post(url, data = {}) {
    const response = await this.api.post(url, data);
    return response.data;
  }

  async put(url, data = {}) {
    const response = await this.api.put(url, data);
    return response.data;
  }

  async patch(url, data = {}) {
    const response = await this.api.patch(url, data);
    return response.data;
  }

  async delete(url) {
    const response = await this.api.delete(url);
    return response.data;
  }
}

export default BaseService;
```

### 2. Admin Service

```javascript
// services/adminService.js
import BaseService from "./baseService";

class AdminService extends BaseService {
  constructor() {
    super("/admin");
  }

  // Platform Statistics
  async getPlatformStats() {
    return this.get("/stats/platform");
  }

  async getActiveBidsStats() {
    return this.get("/active-bids");
  }

  async getCommoditiesStats() {
    return this.get("/commodities/count");
  }

  // User Management
  async getAllUsers(params = {}) {
    return this.get("/users", params);
  }

  async getUserDetails(userId) {
    return this.get(`/users/${userId}`);
  }

  async updateUserVerification(userId, isVerified, notes = "") {
    return this.patch(`/users/${userId}/verification`, {
      is_verified: isVerified,
      verification_notes: notes,
    });
  }

  async deleteUser(userId) {
    return this.delete(`/users/${userId}`);
  }

  async getRecentUsers() {
    return this.get("/users", { limit: 10, sort: "created_at", order: "desc" });
  }

  // Commodity Management
  async getPendingCommodities() {
    return this.get("/pending-commodities/");
  }

  async approveCommodity(commodityId, isApproved, notes = "") {
    return this.post(`/approve-commodity/${commodityId}`, {
      is_approved: isApproved,
      approval_notes: notes,
    });
  }

  // System Health
  async getSystemHealth() {
    try {
      const [dbHealth, redisHealth] = await Promise.all([
        this.checkDatabaseHealth(),
        this.checkRedisHealth(),
      ]);

      return {
        data: {
          database: dbHealth.data,
          redis: redisHealth.data,
          api: { status: "healthy" },
          ml: { status: "healthy" },
        },
      };
    } catch (error) {
      return {
        data: {
          database: { status: "error" },
          redis: { status: "error" },
          api: { status: "error" },
          ml: { status: "error" },
        },
      };
    }
  }

  async checkDatabaseHealth() {
    return this.get("/health/database");
  }

  async checkRedisHealth() {
    return this.get("/health/redis");
  }

  // Bulk Operations
  async bulkApproveUsers(userIds) {
    return this.post("/bulk/approve-users", { user_ids: userIds });
  }

  async bulkDeleteUsers(userIds) {
    return this.post("/bulk/delete-users", { user_ids: userIds });
  }

  async bulkApproveCommodities(commodityIds) {
    return this.post("/bulk/approve-commodities", {
      commodity_ids: commodityIds,
    });
  }
}

export const adminService = new AdminService();
```

### 3. Farmer Service

```javascript
// services/farmerService.js
import BaseService from "./baseService";

class FarmerService extends BaseService {
  constructor() {
    super("/seller");
  }

  // Profile Management
  async getProfile() {
    return this.get("/");
  }

  async updateProfile(profileData) {
    return this.put("/", profileData);
  }

  // Listings Management
  async getMyListings(params = {}) {
    return this.get("/listings", params);
  }

  async createListing(listingData) {
    return this.post("/listings", listingData);
  }

  async updateListing(listingId, listingData) {
    return this.put(`/listings/${listingId}`, listingData);
  }

  async deleteListing(listingId) {
    return this.delete(`/listings/${listingId}`);
  }

  async getListingDetails(listingId) {
    return this.get(`/listings/${listingId}`);
  }

  // Analytics
  async getAnalytics(timeframe = "30") {
    return this.get("/analytics", { days: timeframe });
  }

  async getRevenueStats() {
    return this.get("/revenue");
  }

  async getBidsOnMyListings() {
    return this.get("/bids");
  }
}

export const farmerService = new FarmerService();
```

### 4. Trader Service

```javascript
// services/traderService.js
import BaseService from "./baseService";

class TraderService extends BaseService {
  constructor() {
    super("/bidding");
  }

  // Profile Management
  async getProfile() {
    return this.get("/profile");
  }

  // Bidding
  async getMyBids(params = {}) {
    return this.get("/my-bids", params);
  }

  async placeBid(commodityId, amount) {
    return this.post("/place-bid", {
      commodity_id: commodityId,
      amount: amount,
    });
  }

  async cancelBid(bidId) {
    return this.delete(`/cancel-bid/${bidId}`);
  }

  async getBidHistory(commodityId) {
    return this.get(`/history/${commodityId}`);
  }

  // Watchlist (through separate service)
  async getWatchlist() {
    const watchlistService = new BaseService("/general");
    return watchlistService.get("/watchlist");
  }

  async addToWatchlist(commodityId) {
    const watchlistService = new BaseService("/general");
    return watchlistService.post("/watchlist", { commodity_id: commodityId });
  }

  async removeFromWatchlist(commodityId) {
    const watchlistService = new BaseService("/general");
    return watchlistService.delete(`/watchlist/${commodityId}`);
  }
}

export const traderService = new TraderService();
```

### 5. Commodity Service

```javascript
// services/commodityService.js
import BaseService from "./baseService";

class CommodityService extends BaseService {
  constructor() {
    super("/commodities");
  }

  // Public commodity browsing
  async getAllCommodities(params = {}) {
    return this.get("/", params);
  }

  async getCommodityDetails(commodityId) {
    return this.get(`/${commodityId}`);
  }

  async searchCommodities(query, filters = {}) {
    return this.get("/search", { q: query, ...filters });
  }

  async getCommoditiesByCategory(category, params = {}) {
    return this.get(`/category/${category}`, params);
  }

  // Farmer-specific methods
  async getMyListings(params = {}) {
    return this.get("/my-listings/", params);
  }

  async createListing(listingData) {
    return this.post("/", listingData);
  }

  async updateListing(commodityId, listingData) {
    return this.put(`/${commodityId}`, listingData);
  }

  async deleteListing(commodityId) {
    return this.delete(`/${commodityId}`);
  }

  // Categories
  async getCategories() {
    return this.get("/categories");
  }

  async getCategoryDetails(categorySlug) {
    return this.get(`/categories/${categorySlug}`);
  }
}

export const commodityService = new CommodityService();
```

This is Part 3 of the guide. Should I continue with Part 4 covering ML services, utility functions, and final implementation details?
