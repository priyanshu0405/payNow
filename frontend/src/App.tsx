import React, { useState, useCallback } from 'react';
import axios, { AxiosError } from 'axios';
import { v4 as uuidv4 } from 'uuid';

// --- TYPE DEFINITIONS ---
enum Decision {
  ALLOW = "allow",
  REVIEW = "review",
  BLOCK = "block",
}

interface AgentTraceStep {
  step: string;
  detail: string;
}

interface PaymentResponse {
  decision: Decision;
  reasons: string[];
  agentTrace: AgentTraceStep[];
  requestId: string;
}

// --- UI COMPONENTS ---
const Card: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div className="bg-white shadow-md rounded-lg p-6 mb-6">
    <h2 className="text-xl font-semibold mb-4 text-gray-700 border-b pb-2">{title}</h2>
    {children}
  </div>
);

const AgentTrace: React.FC<{ trace: AgentTraceStep[] }> = ({ trace }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="mt-4">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="text-sm font-medium text-blue-600 hover:text-blue-800"
        aria-expanded={isOpen}
      >
        {isOpen ? 'Hide' : 'Show'} Agent Trace
      </button>
      {isOpen && (
        <div className="mt-2 p-3 bg-gray-50 rounded-md border text-xs text-gray-600 font-mono">
          {trace.map((step, index) => (
            <p key={index} className="whitespace-pre-wrap">
              <span className="font-bold">{step.step}:</span> {step.detail}
            </p>
          ))}
        </div>
      )}
    </div>
  );
};

const ResultDisplay: React.FC<{ response: PaymentResponse; latency: number }> = ({ response, latency }) => {
  const getDecisionAppearance = () => {
    switch (response.decision) {
      case Decision.ALLOW: return { bg: 'bg-green-100', text: 'text-green-800', border: 'border-green-400' };
      case Decision.REVIEW: return { bg: 'bg-yellow-100', text: 'text-yellow-800', border: 'border-yellow-400' };
      case Decision.BLOCK: return { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-400' };
    }
  };
  const appearance = getDecisionAppearance();
  return (
    <Card title="Payment Decision">
      <div className={`border-l-4 ${appearance.border} ${appearance.bg} p-4 rounded-md`}>
        <h3 className={`text-lg font-bold ${appearance.text}`}>Decision: {response.decision.toUpperCase()}</h3>
        {response.reasons.length > 0 && (
          <div className="mt-2">
            <p className={`font-semibold ${appearance.text}`}>Reasons:</p>
            <ul className="list-disc list-inside">
              {response.reasons.map((reason, i) => <li key={i}>{reason}</li>)}
            </ul>
          </div>
        )}
      </div>
      <p className="text-xs text-gray-500 mt-3">Request fulfilled in {latency.toFixed(2)}ms (Request ID: {response.requestId})</p>
      <AgentTrace trace={response.agentTrace} />
    </Card>
  );
};

// --- MAIN APP COMPONENT ---
function App() {
  const [amount, setAmount] = useState('125.50');
  const [payeeId, setPayeeId] = useState('p_789');
  const [customerId, setCustomerId] = useState('c_123');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [paymentResponse, setPaymentResponse] = useState<PaymentResponse | null>(null);
  const [latency, setLatency] = useState(0);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setPaymentResponse(null);
    const startTime = performance.now();
    try {
      const response = await axios.post<PaymentResponse>(
        'http://127.0.0.1:8000/payments/decide',
        { customerId, amount: parseFloat(amount), currency: 'USD', payeeId },
        { headers: { 'X-API-Key': 'your-super-secret-key', 'Idempotency-Key': uuidv4() } }
      );
      setPaymentResponse(response.data);
    } catch (err) {
      const axiosError = err as AxiosError<{ detail: string }>;
      setError(axiosError.response?.data?.detail || 'An unexpected error occurred.');
    } finally {
      setIsLoading(false);
      const endTime = performance.now();
      setLatency(endTime - startTime);
    }
  }, [amount, payeeId, customerId]);

  return (
    <div className="bg-gray-50 min-h-screen flex items-center justify-center font-sans">
      <main className="w-full max-w-lg p-4">
        <header className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-800">PayNow Service</h1>
            <p className="text-gray-600">Enter payment details to get an AI-assisted decision.</p>
        </header>
        <Card title="New Payment">
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label htmlFor="amount" className="block text-sm font-medium text-gray-700 mb-1">Amount (USD)</label>
              <input type="number" id="amount" value={amount} onChange={(e) => setAmount(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" required step="0.01" />
            </div>
            <div className="mb-6">
              <label htmlFor="payeeId" className="block text-sm font-medium text-gray-700 mb-1">Payee ID</label>
              <input type="text" id="payeeId" value={payeeId} onChange={(e) => setPayeeId(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" required />
            </div>
            <button type="submit" disabled={isLoading} className="w-full bg-indigo-600 text-white font-bold py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400">
              {isLoading ? 'Processing...' : 'Submit Payment'}
            </button>
          </form>
        </Card>
        {error && (<div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 rounded-md mb-6" role="alert"><p><span className="font-bold">Error:</span> {error}</p></div>)}
        {paymentResponse && <ResultDisplay response={paymentResponse} latency={latency} />}
      </main>
    </div>
  );
}

export default App;