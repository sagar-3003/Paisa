import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const BASE = import.meta.env.VITE_API_BASE_URL || '';

const VOUCHER_TYPES = [
  { value: 'all', label: 'All Vouchers' },
  { value: 'sales', label: 'Sales' },
  { value: 'purchase', label: 'Purchase' },
  { value: 'expense', label: 'Expense' },
  { value: 'payment_received', label: 'Payment Received' },
  { value: 'payment_made', label: 'Payment Made' },
];

const CREDIT_INTENTS = new Set(['sales', 'payment_received']);

function fmt(amount) {
  return `₹${(amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function intentLabel(intent) {
  return intent?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) || '—';
}

export default function TallyLedger() {
  const today = new Date().toISOString().split('T')[0];
  const firstOfMonth = new Date(new Date().getFullYear(), new Date().getMonth(), 1)
    .toISOString().split('T')[0];

  const [fromDate, setFromDate] = useState(firstOfMonth);
  const [toDate, setToDate] = useState(today);
  const [voucherType, setVoucherType] = useState('all');
  const [rows, setRows] = useState([]);
  const [totals, setTotals] = useState({ total_debit: 0, total_credit: 0, balance: 0, total_count: 0 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [downloading, setDownloading] = useState(null);

  const fetchLedger = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = { from_date: fromDate, to_date: toDate, type: voucherType, page, page_size: 50 };
      const res = await axios.get(`${BASE}/api/tally/ledger`, { params });
      setRows(res.data.rows);
      setTotals({
        total_debit: res.data.total_debit,
        total_credit: res.data.total_credit,
        balance: res.data.balance,
        total_count: res.data.total_count,
      });
    } catch (e) {
      setError('Failed to load ledger. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  }, [fromDate, toDate, voucherType, page]);

  useEffect(() => { fetchLedger(); }, [fetchLedger]);

  const downloadXml = async (row) => {
    setDownloading(row.id);
    try {
      const res = await fetch(`${BASE}/api/tally/download/${row.id}`);
      if (!res.ok) throw new Error('Download failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `paisa_voucher_${row.id.slice(0, 8)}.xml`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      alert('Failed to download XML for this entry.');
    } finally {
      setDownloading(null);
    }
  };

  const totalPages = Math.ceil(totals.total_count / 50);

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Tally Ledger</h1>
          <p className="text-sm text-slate-500 mt-0.5">Day Book — Incoming &amp; Outgoing Entries</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-slate-400 uppercase tracking-wider">Net Balance</p>
          <p className={`text-2xl font-bold ${totals.balance >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
            {fmt(Math.abs(totals.balance))}
            <span className="text-sm ml-1">{totals.balance >= 0 ? 'CR' : 'DR'}</span>
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 mb-6 flex flex-wrap gap-4 items-end shadow-sm">
        <div>
          <label className="block text-xs font-semibold text-slate-500 mb-1 uppercase tracking-wider">From Date</label>
          <input
            type="date" value={fromDate} onChange={e => { setFromDate(e.target.value); setPage(1); }}
            className="border border-slate-300 rounded-lg px-3 py-1.5 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-300"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-500 mb-1 uppercase tracking-wider">To Date</label>
          <input
            type="date" value={toDate} onChange={e => { setToDate(e.target.value); setPage(1); }}
            className="border border-slate-300 rounded-lg px-3 py-1.5 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-300"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-500 mb-1 uppercase tracking-wider">Voucher Type</label>
          <select
            value={voucherType} onChange={e => { setVoucherType(e.target.value); setPage(1); }}
            className="border border-slate-300 rounded-lg px-3 py-1.5 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-300 bg-white"
          >
            {VOUCHER_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
        </div>
        <button
          onClick={() => { setPage(1); fetchLedger(); }}
          className="bg-indigo-600 text-white text-sm font-semibold px-4 py-1.5 rounded-lg hover:bg-indigo-700 transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4">
          <p className="text-xs font-semibold text-emerald-600 uppercase tracking-wider">Total Credit (Income)</p>
          <p className="text-2xl font-bold text-emerald-700 mt-1">{fmt(totals.total_credit)}</p>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <p className="text-xs font-semibold text-red-600 uppercase tracking-wider">Total Debit (Expense)</p>
          <p className="text-2xl font-bold text-red-700 mt-1">{fmt(totals.total_debit)}</p>
        </div>
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
          <p className="text-xs font-semibold text-slate-600 uppercase tracking-wider">Entries</p>
          <p className="text-2xl font-bold text-slate-700 mt-1">{totals.total_count}</p>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400">Loading ledger...</div>
        ) : error ? (
          <div className="p-12 text-center text-red-500">{error}</div>
        ) : rows.length === 0 ? (
          <div className="p-12 text-center text-slate-400">No entries found for the selected filters.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Voucher Type</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Party Name</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-red-500 uppercase tracking-wider">Debit (Dr)</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-emerald-600 uppercase tracking-wider">Credit (Cr)</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">GST</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wider">Tally XML</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {rows.map(row => {
                  const isCredit = CREDIT_INTENTS.has(row.voucher_type);
                  return (
                    <tr
                      key={row.id}
                      className={`transition-colors hover:bg-slate-50 ${isCredit ? 'bg-emerald-50/30' : 'bg-red-50/20'}`}
                    >
                      <td className="px-4 py-3 text-slate-600 whitespace-nowrap">
                        {row.date ? new Date(row.date).toLocaleDateString('en-IN') : '—'}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded-md text-xs font-semibold ${
                          isCredit ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                        }`}>
                          {intentLabel(row.voucher_type)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-800 font-medium">{row.party_name}</td>
                      <td className="px-4 py-3 text-right text-red-600 font-medium">
                        {row.debit > 0 ? fmt(row.debit) : <span className="text-slate-300">—</span>}
                      </td>
                      <td className="px-4 py-3 text-right text-emerald-600 font-medium">
                        {row.credit > 0 ? fmt(row.credit) : <span className="text-slate-300">—</span>}
                      </td>
                      <td className="px-4 py-3 text-right text-slate-500">
                        {row.gst_amount > 0 ? fmt(row.gst_amount) : <span className="text-slate-300">—</span>}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                          row.payment_status === 'paid'
                            ? 'bg-emerald-100 text-emerald-700'
                            : row.payment_status === 'partial'
                            ? 'bg-amber-100 text-amber-700'
                            : 'bg-slate-100 text-slate-600'
                        }`}>
                          {row.payment_status?.toUpperCase() || 'PENDING'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <button
                          onClick={() => downloadXml(row)}
                          disabled={downloading === row.id}
                          title="Download Tally XML"
                          className="inline-flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800 font-semibold disabled:opacity-40 transition-colors"
                        >
                          {downloading === row.id ? (
                            'Downloading...'
                          ) : (
                            <>
                              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="w-3.5 h-3.5">
                                <path d="M8 1a.75.75 0 0 1 .75.75v5.69l1.97-1.97a.75.75 0 0 1 1.06 1.06L8.53 9.78a.75.75 0 0 1-1.06 0L4.22 6.53a.75.75 0 0 1 1.06-1.06L7.25 7.44V1.75A.75.75 0 0 1 8 1ZM3.5 12.25a.75.75 0 0 1 .75-.75h7.5a.75.75 0 0 1 0 1.5h-7.5a.75.75 0 0 1-.75-.75Z" />
                              </svg>
                              XML
                            </>
                          )}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
              {/* Totals row */}
              <tfoot>
                <tr className="bg-slate-100 border-t-2 border-slate-300 font-bold text-sm">
                  <td colSpan={3} className="px-4 py-3 text-slate-700">Total ({totals.total_count} entries)</td>
                  <td className="px-4 py-3 text-right text-red-700">{fmt(totals.total_debit)}</td>
                  <td className="px-4 py-3 text-right text-emerald-700">{fmt(totals.total_credit)}</td>
                  <td colSpan={3} className="px-4 py-3 text-right text-slate-600">
                    Balance: <span className={totals.balance >= 0 ? 'text-emerald-700' : 'text-red-700'}>
                      {fmt(Math.abs(totals.balance))} {totals.balance >= 0 ? 'CR' : 'DR'}
                    </span>
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <p className="text-sm text-slate-500">
            Page {page} of {totalPages} ({totals.total_count} entries)
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 text-sm border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-50 disabled:opacity-40 transition-colors"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1.5 text-sm border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-50 disabled:opacity-40 transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
