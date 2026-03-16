import React, { useState, useEffect } from 'react';
import axios from 'axios';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/dashboard');
        setStats(response.data);
      } catch (error) {
        console.error('Error fetching dashboard stats', error);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) return <div className="p-8 text-center text-gray-500">Loading Dashboard...</div>;
  if (!stats) return <div className="p-8 text-center text-red-500">Failed to load Dashboard data</div>;

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-8 text-gray-800">Paisa Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        
        {/* Today's Sales */}
        <div className="bg-white rounded-xl shadow p-6 border-l-4 border-green-500 bg-gradient-to-r from-green-50 to-white">
          <div className="text-sm text-gray-500 uppercase tracking-widest font-semibold">Today's Sales</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">₹{stats.today_sales.toLocaleString('en-IN')}</div>
        </div>

        {/* GST Payable */}
        <div className="bg-white rounded-xl shadow p-6 border-l-4 border-blue-500">
          <div className="text-sm text-gray-500 uppercase tracking-widest font-semibold">GST Payable (This Month)</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">₹{stats.gst_payable.toLocaleString('en-IN')}</div>
          <div className="text-xs text-gray-400 mt-1">Due Date: {new Date(stats.gst_due_date).toLocaleDateString()}</div>
        </div>

        {/* Pending Dues */}
        <div className={`bg-white rounded-xl shadow p-6 border-l-4 ${stats.pending_dues > 0 ? 'border-amber-500 bg-amber-50' : 'border-gray-200'}`}>
          <div className="text-sm text-gray-500 uppercase tracking-widest font-semibold">Pending Dues</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">₹{stats.pending_dues.toLocaleString('en-IN')}</div>
          <div className="text-xs text-gray-500 mt-1">From {stats.pending_dues_parties} parties</div>
        </div>

        {/* Overdue Reminders */}
        <div className={`bg-white rounded-xl shadow p-6 border-l-4 ${stats.overdue_count > 0 ? 'border-red-500 bg-red-50' : 'border-gray-200'}`}>
          <div className="text-sm text-gray-500 uppercase tracking-widest font-semibold">Overdue Invoices</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">{stats.overdue_count}</div>
          {stats.overdue_count > 0 && (
            <button className="mt-4 bg-red-500 text-white text-xs px-3 py-1 rounded shadow hover:bg-red-600 transition">
              Send Reminders
            </button>
          )}
        </div>

        {/* TDS Deducted */}
        <div className="bg-white rounded-xl shadow p-6 border-l-4 border-purple-500">
          <div className="text-sm text-gray-500 uppercase tracking-widest font-semibold">TDS Deducted (This Month)</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">₹{stats.tds_deducted.toLocaleString('en-IN')}</div>
        </div>

        {/* Low Stock Alerts */}
        <div className={`bg-white rounded-xl shadow p-6 border-l-4 ${stats.low_stock_items.length > 0 ? 'border-orange-500' : 'border-gray-200'}`}>
          <div className="text-sm text-gray-500 uppercase tracking-widest font-semibold">Low Stock Items</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">{stats.low_stock_items.length}</div>
          {stats.low_stock_items.length > 0 && (
            <div className="text-xs text-gray-500 mt-2">
              {stats.low_stock_items.slice(0, 3).join(', ')} {stats.low_stock_items.length > 3 ? '...' : ''}
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default Dashboard;
