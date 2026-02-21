const API_BASE = import.meta.env.VITE_API_URL ?? "";
const API = API_BASE ? `${API_BASE.replace(/\/$/, "")}/api` : "/api";

export type SymbolsResponse = { symbols: string[] };
export type ObserversResponse = Record<string, string>;
export type HistoryItem = {
  symbol: string;
  target: number;
  price: number;
  at: string;
};
export type HistoryResponse = { history: HistoryItem[] };

export type MatchPriceItem = {
  symbol: string;
  target: number;
  price: number;
  at: string;
};
export type MatchPriceResponse = { match_price: MatchPriceItem[] };

export async function fetchSymbols(): Promise<string[]> {
  const res = await fetch(`${API}/symbols`);
  const data: SymbolsResponse = await res.json();
  return data.symbols ?? [];
}

export async function fetchObservers(): Promise<ObserversResponse> {
  const res = await fetch(`${API}/observers`);
  const data: ObserversResponse = await res.json();
  return data ?? {};
}

export async function saveObservers(
  observers: Record<string, string>
): Promise<void> {
  await fetch(`${API}/observers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(observers),
  });
}

export async function fetchHistory(symbol?: string): Promise<HistoryItem[]> {
  const url = symbol
    ? `${API}/history?symbol=${encodeURIComponent(symbol)}`
    : `${API}/history`;
  const res = await fetch(url);
  const data: HistoryResponse = await res.json();
  return data.history ?? [];
}

export async function fetchMatchPrice(
  symbol?: string
): Promise<MatchPriceItem[]> {
  const url = symbol
    ? `${API}/match-price?symbol=${encodeURIComponent(symbol)}`
    : `${API}/match-price`;
  const res = await fetch(url);
  const data: MatchPriceResponse = await res.json();
  return data.match_price ?? [];
}

export type PriceResponse = { symbol: string; price: number };
export type PriceErrorResponse = { error: string };

export async function fetchCurrentPrice(
  symbol: string
): Promise<{ symbol: string; price: number } | { error: string }> {
  const sym = symbol.trim().toUpperCase();
  if (!sym) return { error: "Symbol is required" };
  const res = await fetch(`${API}/price?symbol=${encodeURIComponent(sym)}`);
  const data = await res.json();
  if (!res.ok)
    return {
      error: (data as PriceErrorResponse).error ?? "Failed to get price",
    };
  return data as PriceResponse;
}
