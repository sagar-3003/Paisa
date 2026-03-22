import React, { useState } from 'react';

const CREDIT_INTENTS = ['sales', 'payment_received'];

function EntryCard({ data }) {
  const isSales = CREDIT_INTENTS.includes(data.intent);
  const [saving, setSaving] = useState(false);
  const [savedId, setSavedId] = useState(null);
  const [saveError, setSaveError] = useState(null);

  const handleSaveAndDownload = async () => {
    setSaving(true);
    setSaveError(null);
    try {
      // 1. Save transaction to DB
      const BASE = import.meta.env.VITE_API_BASE_URL || '';
      let txnId = savedId;

      if (!txnId) {
        const saveRes = await fetch(`${BASE}/api/transactions/save`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            intent: data.intent,
            party_name: data.party_name,
            party_gstin: data.party_gstin,
            party_state: data.party_state,
            total_amount: data.total_amount,
            gst_amount: data.gst_amount,
            tds_amount: data.tds_amount || 0,
            net_amount: data.total_amount,
            payment_status: data.payment_status || 'pending',
            source_type: 'chat',
            raw_input: data.raw_input,
            date: data.date,
          }),
        });
        if (!saveRes.ok) throw new Error('Failed to save transaction');
        const saved = await saveRes.json();
        txnId = saved.transaction_id;
        setSavedId(txnId);
      }

      // 2. Download XML
      const xmlRes = await fetch(`${BASE}/api/tally/download/${txnId}`);
      if (!xmlRes.ok) throw new Error('Failed to generate XML');
      const blob = await xmlRes.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `paisa_voucher_${txnId.slice(0, 8)}.xml`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setSaveError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="bg-slate-50 rounded-xl p-5 border border-slate-200 mt-2 text-sm w-80">
      <div className="flex justify-between items-center mb-4">
        <span className={`px-2.5 py-1 uppercase text-xs font-bold rounded-lg tracking-wider ${isSales ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
          {data.intent}
        </span>
        <span className="text-slate-500 font-medium">{data.date}</span>
      </div>

      <div className="mb-4">
        <h3 className="text-lg font-bold text-slate-800">{data.party_name || 'Cash Party'}</h3>
        <p className="text-slate-500 font-medium">
          Status:{' '}
          <span className={data.payment_status === 'paid' ? 'text-emerald-600' : 'text-amber-600'}>
            {data.payment_status?.toUpperCase() || 'UNKNOWN'}
          </span>
        </p>
      </div>

      <div className="bg-white border rounded-lg p-3 mb-4 space-y-2 shadow-sm">
        {data.items && data.items.map((item, idx) => (
          <div key={idx} className="flex justify-between font-medium text-slate-700">
            <span>{item.description}</span>
            <span>₹{item.amount?.toLocaleString()}</span>
          </div>
        ))}
      </div>

      <div className="flex justify-between items-center text-lg font-bold text-slate-900 border-t pt-3">
        <span>Total</span>
        <span>₹{data.total_amount?.toLocaleString()}</span>
      </div>

      {saveError && (
        <p className="mt-2 text-xs text-red-500">{saveError}</p>
      )}

      <div className="mt-5 flex gap-2">
        <button
          onClick={() => alert('Edit functionality coming soon!')}
          className="flex-1 bg-white border border-slate-300 text-slate-700 font-semibold py-2 rounded-lg hover:bg-slate-50 cursor-pointer transition-colors shadow-sm active:scale-95"
        >
          Edit
        </button>
        <button
          onClick={handleSaveAndDownload}
          disabled={saving}
          className={`flex-1 text-white font-semibold py-2 rounded-lg cursor-pointer transition-all shadow-sm active:scale-95 flex items-center justify-center gap-1.5 ${
            savedId ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-slate-900 hover:bg-slate-800'
          } disabled:opacity-60`}
        >
          {saving ? (
            'Saving...'
          ) : savedId ? (
            <>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                <path fillRule="evenodd" d="M10 3a.75.75 0 0 1 .75.75v4.5h4.5a.75.75 0 0 1 0 1.5h-4.5v4.5a.75.75 0 0 1-1.5 0v-4.5h-4.5a.75.75 0 0 1 0-1.5h4.5v-4.5A.75.75 0 0 1 10 3Z" clipRule="evenodd" />
              </svg>
              Download XML
            </>
          ) : (
            <>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                <path fillRule="evenodd" d="M10 3a.75.75 0 0 1 .75.75v7.69l2.47-2.47a.75.75 0 1 1 1.06 1.06l-3.75 3.75a.75.75 0 0 1-1.06 0L5.72 9.06a.75.75 0 0 1 1.06-1.06L9.25 10.44V3.75A.75.75 0 0 1 10 3ZM5 17.25a.75.75 0 0 1 .75-.75h8.5a.75.75 0 0 1 0 1.5h-8.5a.75.75 0 0 1-.75-.75Z" clipRule="evenodd" />
              </svg>
              Save &amp; Tally XML
            </>
          )}
        </button>
      </div>
    </div>
  );
}

export default EntryCard;
