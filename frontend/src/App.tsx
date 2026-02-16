import { useEffect, useState } from "react";
import {
  fetchHistory,
  fetchObservers,
  fetchSymbols,
  saveObservers,
  type HistoryItem,
} from "./api";
import "./App.css";

function App() {
  const [symbols, setSymbols] = useState<string[]>([]);
  const [observerValues, setObserverValues] = useState<Record<string, string>>(
    {}
  );
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [filterSymbol, setFilterSymbol] = useState<string>("");
  const [toast, setToast] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchSymbols(), fetchObservers()]).then(([symList, obs]) => {
      setSymbols(symList);
      setObserverValues(obs);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    fetchHistory(filterSymbol || undefined).then(setHistory);
  }, [filterSymbol]);

  const handleSave = async () => {
    const trimmed: Record<string, string> = {};
    for (const [k, v] of Object.entries(observerValues)) {
      if (k && v?.trim()) trimmed[k] = v.trim();
    }
    await saveObservers(trimmed);
    setObserverValues((prev) => ({ ...prev, ...trimmed }));
    setToast(true);
    setTimeout(() => setToast(false), 2000);
  };

  const setObserver = (symbol: string, value: string) => {
    setObserverValues((prev) => ({ ...prev, [symbol]: value }));
  };

  const refreshHistory = () => {
    fetchHistory(filterSymbol || undefined).then(setHistory);
  };

  if (loading) {
    return (
      <div className="app">
        <p className="sub">Loading…</p>
      </div>
    );
  }

  return (
    <div className="app">
      <h1>Vietnam Stock Observer</h1>
      <p className="sub">
        Set a target price per symbol. When price is at or below target, you get
        a Telegram alert. Check runs every 5 minutes.
      </p>

      <section className="card">
        <h2>Observer prices (alert when price ≤ value)</h2>
        <div className="symbol-grid">
          {symbols.map((sym) => (
            <div key={sym} className="symbol-row">
              <label>{sym}</label>
              <input
                type="text"
                placeholder="e.g. 95500"
                value={observerValues[sym] ?? ""}
                onChange={(e) => setObserver(sym, e.target.value)}
              />
            </div>
          ))}
        </div>
        <p className="actions">
          <button type="button" onClick={handleSave}>
            Save observer prices
          </button>
        </p>
      </section>

      <section className="card">
        <h2>Alert history</h2>
        <div className="filter-row">
          <label htmlFor="filterSymbol">Filter by symbol:</label>
          <select
            id="filterSymbol"
            value={filterSymbol}
            onChange={(e) => setFilterSymbol(e.target.value)}
          >
            <option value="">All symbols</option>
            {symbols.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <button type="button" onClick={refreshHistory}>
            Refresh
          </button>
        </div>
        <table>
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Target</th>
              <th>Price</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {history.length === 0 ? (
              <tr>
                <td colSpan={4} className="empty">
                  No alerts yet.
                </td>
              </tr>
            ) : (
              history.map((h, i) => (
                <tr key={`${h.symbol}-${h.at}-${i}`}>
                  <td>{h.symbol}</td>
                  <td>
                    {typeof h.target === "number"
                      ? h.target.toLocaleString()
                      : h.target}
                  </td>
                  <td>
                    {typeof h.price === "number"
                      ? h.price.toLocaleString()
                      : h.price}
                  </td>
                  <td>{h.at}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>

      {toast && <div className="toast">Saved.</div>}
    </div>
  );
}

export default App;
