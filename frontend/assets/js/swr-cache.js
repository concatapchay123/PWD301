/**
 * PWD301 LMS - SWR (Stale-While-Revalidate) Cache Engine
 * Provides instant in-memory responses (<50ms) for high-frequency navigation
 * with background revalidation and automatic CUD invalidation.
 */
class SWRCache {
  static _store = new Map();
  static _defaultTTL = 3 * 60 * 1000; // 3 minutes default TTL

  /**
   * Get cached data if available and fresh.
   */
  static get(key) {
    const entry = this._store.get(key);
    if (!entry) return null;
    if (Date.now() - entry.timestamp > entry.ttl) {
      return null;
    }
    return entry.data;
  }

  /**
   * Get cached data even if stale, useful for instant rendering.
   */
  static getStale(key) {
    const entry = this._store.get(key);
    return entry ? entry.data : null;
  }

  /**
   * Store data in cache with TTL.
   */
  static set(key, data, ttl = this._defaultTTL) {
    this._store.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
  }

  /**
   * Invalidate specific key or keys matching a regex/prefix.
   */
  static invalidate(pattern) {
    if (!pattern) {
      this._store.clear();
      return;
    }
    const regex = pattern instanceof RegExp ? pattern : new RegExp(pattern);
    for (const key of this._store.keys()) {
      if (regex.test(key)) {
        this._store.delete(key);
      }
    }
  }

  /**
   * Clear all cached data.
   */
  static clear() {
    this._store.clear();
  }

  /**
   * Wrap an async fetcher with SWR semantics:
   * Returns stale data immediately if present, revalidates in the background,
   * or awaits fresh data if cache is empty or force=true.
   */
  static async wrap(key, fetcher, options = {}) {
    const ttl = options.ttl || this._defaultTTL;
    const force = Boolean(options.force);
    const staleData = this.getStale(key);

    if (staleData && !force) {
      // Revalidate in the background asynchronously
      Promise.resolve().then(async () => {
        try {
          const freshData = await fetcher();
          const changed = JSON.stringify(freshData) !== JSON.stringify(staleData);
          this.set(key, freshData, ttl);
          if (changed && typeof options.onRevalidate === 'function') {
            options.onRevalidate(freshData);
          }
        } catch (err) {
          console.warn('[SWRCache] Background revalidation failed for', key, err);
        }
      });
      return staleData;
    }

    // No cache or forced refresh
    const freshData = await fetcher();
    this.set(key, freshData, ttl);
    return freshData;
  }
}

if (typeof window !== 'undefined') {
  window.SWRCache = SWRCache;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = SWRCache;
}
