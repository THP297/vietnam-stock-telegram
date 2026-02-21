import { useEffect, useState } from "react";
import {
  fetchCurrentPrice,
  fetchHistory,
  fetchObserverPriceChange,
  fetchObservers,
  fetchSymbols,
  saveObservers,
  type HistoryItem,
  type ObserverPriceChangeItem,
} from "./api";
import "./App.css";

function App() {
  const [symbols, setSymbols] = useState<string[]>([]);
  const [observerValues, setObserverValues] = useState<Record<string, string>>(
    {}
  );
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [observerPriceChange, setObserverPriceChange] = useState<
    ObserverPriceChangeItem[]
  >([]);
  const [filterSymbol, setFilterSymbol] = useState<string>("");
  const [filterObserverPriceChange, setFilterObserverPriceChange] =
    useState<string>("");
  const [toast, setToast] = useState(false);
  const [loading, setLoading] = useState(true);
  const [newSymbolName, setNewSymbolName] = useState("");
  const [newSymbolPrice, setNewSymbolPrice] = useState("");
  const [page, setPage] = useState<"main" | "add" | "price" | "history">(
    "main"
  );
  const [priceSymbol, setPriceSymbol] = useState("");
  const [priceResult, setPriceResult] = useState<
    { symbol: string; price: number } | { error: string } | null
  >(null);
  const [priceLoading, setPriceLoading] = useState(false);

  const loadFromApi = () => {
    return Promise.all([fetchSymbols(), fetchObservers()]).then(
      ([symList, obs]) => {
        setSymbols(symList);
        setObserverValues(obs);
      }
    );
  };

  useEffect(() => {
    loadFromApi().then(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchHistory(filterSymbol || undefined).then(setHistory);
  }, [filterSymbol]);

  useEffect(() => {
    fetchObserverPriceChange(filterObserverPriceChange || undefined).then(
      setObserverPriceChange
    );
  }, [filterObserverPriceChange]);

  const handleSave = async () => {
    const trimmed: Record<string, string> = {};
    for (const [k, v] of Object.entries(observerValues)) {
      if (k && v?.trim()) trimmed[k] = v.trim();
    }
    await saveObservers(trimmed);
    setObserverValues((prev) => ({ ...prev, ...trimmed }));
    fetchHistory(filterSymbol || undefined).then(setHistory);
    setToast(true);
    setTimeout(() => setToast(false), 2000);
  };

  const setObserver = (symbol: string, value: string) => {
    setObserverValues((prev) => ({ ...prev, [symbol]: value }));
  };

  const refreshHistory = () => {
    fetchHistory(filterSymbol || undefined).then(setHistory);
  };

  const refreshObserverPriceChange = () => {
    fetchObserverPriceChange(filterObserverPriceChange || undefined).then(
      setObserverPriceChange
    );
  };

  const handleRemoveSymbol = async (symbol: string) => {
    const next = { ...observerValues };
    delete next[symbol];
    await saveObservers(next);
    setObserverValues(next);
    await loadFromApi();
    setToast(true);
    setTimeout(() => setToast(false), 2000);
  };

  const handleAddSymbol = async () => {
    const sym = newSymbolName?.trim().toUpperCase();
    const price = newSymbolPrice?.trim();
    if (!sym || !price) return;
    const next = { ...observerValues, [sym]: price };
    await saveObservers(next);
    setObserverValues(next);
    setNewSymbolName("");
    setNewSymbolPrice("");
    setPage("main");
    await loadFromApi();
    setToast(true);
    setTimeout(() => setToast(false), 2000);
  };

  const handleGetPrice = async () => {
    const sym = priceSymbol.trim().toUpperCase();
    if (!sym) return;
    setPriceLoading(true);
    setPriceResult(null);
    try {
      const result = await fetchCurrentPrice(sym);
      setPriceResult(result);
    } finally {
      setPriceLoading(false);
    }
  };

  const canAddSymbol =
    newSymbolName.trim().length > 0 && newSymbolPrice.trim().length > 0;

  if (loading) {
    return (
      <div className="app">
        <p className="sub">Loading…</p>
      </div>
    );
  }

  const navItems = [
    { id: "main" as const, label: "Main", icon: "📋" },
    { id: "add" as const, label: "Add symbol", icon: "➕" },
    { id: "price" as const, label: "Current price", icon: "📈" },
    { id: "history" as const, label: "Alert history", icon: "📜" },
  ];

  return (
    <div className="app">
      <aside className="sidebar">
        <h1 className="sidebar-title">Vietnam Stock</h1>
        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`sidebar-item ${page === item.id ? "active" : ""}`}
              onClick={() => setPage(item.id)}
            >
              <span className="sidebar-icon">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>
      </aside>
      <main className="main-content">
        {page === "main" && (
          <>
            <p className="sub">
              Set a target price per symbol. When live price falls inside the
              band (within 0.1% of target), you get a Telegram alert and a row
              is added to Observer Price Change. Check runs every 30 seconds.
            </p>
            <section className="card">
              <h2>
                Observer prices (alert when price is within 0.1% of target)
              </h2>
              <p className="sub">Data from database only.</p>
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
                    <button
                      type="button"
                      className="btn-remove"
                      onClick={() => handleRemoveSymbol(sym)}
                      title="Remove symbol"
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
              <p className="actions">
                <button type="button" onClick={handleSave}>
                  Save observer prices
                </button>
              </p>
            </section>
            <section className="card" id="observer-price-change">
              <h2>Observer Price Change</h2>
              <p className="sub">
                Rows added when live price falls inside the band (within 0.1% of
                target). One row per (symbol, target) the first time price
                enters the band; Telegram alert is sent at the same time.
              </p>
              <div className="filter-row">
                <label htmlFor="filterObserverPriceChange">
                  Filter by symbol:
                </label>
                <select
                  id="filterObserverPriceChange"
                  value={filterObserverPriceChange}
                  onChange={(e) => setFilterObserverPriceChange(e.target.value)}
                >
                  <option value="">All symbols</option>
                  {symbols.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
                <button type="button" onClick={refreshObserverPriceChange}>
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
                  {observerPriceChange.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="empty">
                        No observer price change rows yet.
                      </td>
                    </tr>
                  ) : (
                    observerPriceChange.map((m, i) => (
                      <tr key={`${m.symbol}-${m.at}-${i}`}>
                        <td>{m.symbol}</td>
                        <td>
                          {typeof m.target === "number"
                            ? m.target.toLocaleString()
                            : m.target}
                        </td>
                        <td>
                          {typeof m.price === "number"
                            ? m.price.toLocaleString()
                            : m.price}
                        </td>
                        <td>{m.at}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </section>
          </>
        )}

        {page === "history" && (
          <section className="card page-card" id="alert-history">
            <h2>Alert history</h2>
            <p className="sub">
              New rows only when you save a changed target price (observer
              save).
            </p>
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
        )}

        {page === "add" && (
          <section className="card page-card">
            <h2>Add symbol</h2>
            <p className="sub">
              Enter symbol and target price. Both are required.
            </p>
            <div className="add-symbol-form">
              <label htmlFor="page-symbol">Symbol</label>
              <input
                id="page-symbol"
                type="text"
                placeholder="e.g. VCB"
                value={newSymbolName}
                onChange={(e) => setNewSymbolName(e.target.value)}
                aria-label="Symbol name"
              />
              <label htmlFor="page-price">Target price</label>
              <input
                id="page-price"
                type="text"
                placeholder="e.g. 95500"
                value={newSymbolPrice}
                onChange={(e) => setNewSymbolPrice(e.target.value)}
                aria-label="Target price"
              />
              <div className="modal-actions">
                <button type="button" onClick={() => setPage("main")}>
                  Cancel
                </button>
                <button
                  type="button"
                  className="btn-add"
                  onClick={handleAddSymbol}
                  disabled={!canAddSymbol}
                  title="Both symbol and price are required"
                >
                  Add symbol
                </button>
              </div>
            </div>
          </section>
        )}

        {page === "price" && (
          <section className="card page-card">
            <h2>Current symbol price</h2>
            <p className="sub">Get live price for a symbol using vnstock.</p>
            <div className="price-lookup">
              <label htmlFor="price-symbol">Symbol</label>
              <div className="price-lookup-row">
                <input
                  id="price-symbol"
                  type="text"
                  placeholder="e.g. VCB, TCB, FPT"
                  value={priceSymbol}
                  onChange={(e) => setPriceSymbol(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleGetPrice()}
                  aria-label="Symbol to look up"
                />
                <button
                  type="button"
                  onClick={handleGetPrice}
                  disabled={!priceSymbol.trim() || priceLoading}
                >
                  {priceLoading ? "Loading…" : "Get price"}
                </button>
              </div>
              {priceResult && (
                <div
                  className={
                    "price-result " +
                    ("error" in priceResult ? "price-error" : "price-ok")
                  }
                >
                  {"error" in priceResult ? (
                    priceResult.error
                  ) : (
                    <>
                      <strong>{priceResult.symbol}</strong>:{" "}
                      {priceResult.price.toLocaleString()}
                    </>
                  )}
                </div>
              )}
            </div>
          </section>
        )}
      </main>

      {toast && <div className="toast">Saved.</div>}
    </div>
  );
}

export default App;
