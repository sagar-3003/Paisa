import React from 'react';

function EntryCard({ data }) {
  const isSales = data.intent === 'sales';
  
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
        <p className="text-slate-500 font-medium">Status: <span className={data.payment_status === 'paid' ? 'text-emerald-600' : 'text-amber-600'}>{data.payment_status?.toUpperCase() || 'UNKNOWN'}</span></p>
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

      <div className="mt-5 flex gap-2">
        <button 
          onClick={() => alert("Edit functionality is coming soon! You will be able to modify the JSON fields here.")}
          className="flex-1 bg-white border border-slate-300 text-slate-700 font-semibold py-2 rounded-lg hover:bg-slate-50 hover:cursor-pointer transition-colors shadow-sm active:scale-95">
          Edit
        </button>
        <button 
          onClick={async (e) => {
            const btn = e.currentTarget;
            btn.innerText = 'Posting...';
            btn.classList.add('opacity-70');
            try {
               await fetch('/api/tally-sync', { method: 'POST' });
               setTimeout(() => {
                 btn.innerText = 'Posted!';
                 btn.classList.remove('bg-slate-900', 'hover:bg-slate-800');
                 btn.classList.add('bg-emerald-600', 'hover:bg-emerald-700');
               }, 1000);
            } catch(e) {
               btn.innerText = 'Error';
            }
          }}
          className="flex-1 bg-slate-900 text-white font-semibold py-2 rounded-lg hover:bg-slate-800 hover:cursor-pointer transition-all shadow-sm active:scale-95">
          Post to Tally
        </button>
      </div>
    </div>
  );
}

export default EntryCard;
