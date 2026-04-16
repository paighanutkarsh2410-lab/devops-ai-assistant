'use client';

/**
 * Simple TTL cache for API responses.
 * Stores data in memory with automatic expiration.
 */

interface CacheEntry<T> {
  data: T;
  expiresAt: number;
}

class APICache {
  private store = new Map<string, CacheEntry<unknown>>();
  private defaultTTL: number;

  constructor(defaultTTLMs = 30000) {
    this.defaultTTL = defaultTTLMs;
  }

  get<T>(key: string): T | null {
    const entry = this.store.get(key);
    if (!entry) return null;
    if (Date.now() > entry.expiresAt) {
      this.store.delete(key);
      return null;
    }
    return entry.data as T;
  }

  set<T>(key: string, data: T, ttlMs?: number): void {
    this.store.set(key, {
      data,
      expiresAt: Date.now() + (ttlMs ?? this.defaultTTL),
    });
  }

  invalidate(keyOrPattern: string): void {
    if (keyOrPattern.includes('*')) {
      const regex = new RegExp('^' + keyOrPattern.replace(/\*/g, '.*') + '$');
      for (const key of this.store.keys()) {
        if (regex.test(key)) this.store.delete(key);
      }
    } else {
      this.store.delete(keyOrPattern);
    }
  }

  clear(): void {
    this.store.clear();
  }

  size(): number {
    // Cleanup expired entries
    const now = Date.now();
    for (const [key, entry] of this.store) {
      if (now > entry.expiresAt) this.store.delete(key);
    }
    return this.store.size;
  }
}

export const apiCache = new APICache(30000); // 30s default TTL

/**
 * Cached fetch wrapper — deduplicates in-flight requests
 */
const inflightRequests = new Map<string, Promise<unknown>>();

export async function cachedFetch<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttlMs = 30000,
): Promise<T> {
  // Check cache
  const cached = apiCache.get<T>(key);
  if (cached !== null) return cached;

  // Deduplicate in-flight
  if (inflightRequests.has(key)) {
    return inflightRequests.get(key) as Promise<T>;
  }

  const promise = fetcher().then((data) => {
    apiCache.set(key, data, ttlMs);
    inflightRequests.delete(key);
    return data;
  }).catch((err) => {
    inflightRequests.delete(key);
    throw err;
  });

  inflightRequests.set(key, promise);
  return promise;
}
