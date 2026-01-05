/**
 * Application constants
 */

// Polling intervals (in milliseconds)
export const POLLING_INTERVALS = {
  POLICY_LOGS: 5000,      // 5 seconds
  A2A_NETWORK: 10000,     // 10 seconds
  FALLBACK_POLL: 5000,    // 5 seconds (WebSocket fallback)
} as const;

// WebSocket configuration
export const WEBSOCKET_CONFIG = {
  RECONNECT_DELAY: 1000,
  MAX_RECONNECT_DELAY: 30000,
  PING_INTERVAL: 30000,
  MAX_RECONNECT_ATTEMPTS: 10,
} as const;

// API configuration
export const API_CONFIG = {
  TIMEOUT: 30000,
  MAX_RETRIES: 3,
  RETRY_DELAY: 1000,
} as const;
