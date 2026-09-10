// services/api.ts

import axios, {
  AxiosError,
  AxiosInstance,
  AxiosRequestConfig,
  InternalAxiosRequestConfig,
} from "axios";
import * as SecureStore from "expo-secure-store";
import { jwtDecode, JwtPayload } from "jwt-decode";
import { Platform } from "react-native";

/* -------------------------------------------------------------------------- */
/* API configuration                                                          */
/* -------------------------------------------------------------------------- */

/**
 * Expo environment variable.
 *
 * In .env:
 *
 * EXPO_PUBLIC_DJANGO_API_URL=http://192.168.1.100:8000
 *
 * IMPORTANT:
 * For a physical phone, do NOT use 127.0.0.1 or localhost.
 * Use the LAN IP address of the machine running Django.
 */
export const API_BASE =
  process.env.EXPO_PUBLIC_DJANGO_API_URL ||
  "http://127.0.0.1:8000"

/* -------------------------------------------------------------------------- */
/* Types                                                                      */
/* -------------------------------------------------------------------------- */

export interface TokenPayload extends JwtPayload {
  user_id?: number;
  is_superuser?: boolean;
  isSuperuser?: boolean;
  role?: string;
  role_name?: string;
  email?: string;
}

export interface RefreshResponse {
  access: string;
  refresh?: string;
}

export interface RetryableRequestConfig extends AxiosRequestConfig {
  _retry?: boolean;
  _refreshAttempted?: boolean;
}

export interface ApiError {
  detail?: string;
  error?: string | Record<string, string[]>;
  message?: string;
  code?: string;
}

/* -------------------------------------------------------------------------- */
/* Secure Token Storage                                                       */
/* -------------------------------------------------------------------------- */

const ACCESS_TOKEN_KEY = "auth_access_token";
const REFRESH_TOKEN_KEY = "auth_refresh_token";

/**
 * Platform-aware secure storage.
 * 
 * In production, use SecureStore for both platforms.
 * In development, fallback to AsyncStorage for debugging.
 */
const isDevelopment = __DEV__;

const storage = {
  getItem: async (key: string): Promise<string | null> => {
    try {
      if (Platform.OS === "web") {
        return localStorage.getItem(key);
      }
      
      if (isDevelopment) {
        // Use AsyncStorage in dev for easier debugging
        const { default: AsyncStorage } = await import(
          "@react-native-async-storage/async-storage"
        );
        return await AsyncStorage.getItem(key);
      }
      
      return await SecureStore.getItemAsync(key);
    } catch (error) {
      console.error(`Failed to read ${key}:`, error);
      return null;
    }
  },

  setItem: async (key: string, value: string): Promise<void> => {
    try {
      if (Platform.OS === "web") {
        localStorage.setItem(key, value);
        return;
      }
      
      if (isDevelopment) {
        const { default: AsyncStorage } = await import(
          "@react-native-async-storage/async-storage"
        );
        await AsyncStorage.setItem(key, value);
        return;
      }
      
      await SecureStore.setItemAsync(key, value);
    } catch (error) {
      console.error(`Failed to store ${key}:`, error);
      throw error;
    }
  },

  removeItem: async (key: string): Promise<void> => {
    try {
      if (Platform.OS === "web") {
        localStorage.removeItem(key);
        return;
      }
      
      if (isDevelopment) {
        const { default: AsyncStorage } = await import(
          "@react-native-async-storage/async-storage"
        );
        await AsyncStorage.removeItem(key);
        return;
      }
      
      await SecureStore.deleteItemAsync(key);
    } catch (error) {
      console.error(`Failed to remove ${key}:`, error);
      throw error;
    }
  },

  multiRemove: async (keys: string[]): Promise<void> => {
    try {
      if (Platform.OS === "web") {
        keys.forEach((key) => localStorage.removeItem(key));
        return;
      }
      
      if (isDevelopment) {
        const { default: AsyncStorage } = await import(
          "@react-native-async-storage/async-storage"
        );
        await AsyncStorage.multiRemove(keys);
        return;
      }
      
      await Promise.all(keys.map((key) => SecureStore.deleteItemAsync(key)));
    } catch (error) {
      console.error("Failed to remove tokens:", error);
      throw error;
    }
  },
};

export const getAccessToken = async (): Promise<string | null> => {
  return storage.getItem(ACCESS_TOKEN_KEY);
};

export const getRefreshToken = async (): Promise<string | null> => {
  return storage.getItem(REFRESH_TOKEN_KEY);
};

export const setTokens = async (
  access: string,
  refresh?: string | null
): Promise<void> => {
  await storage.setItem(ACCESS_TOKEN_KEY, access);
  if (refresh) {
    await storage.setItem(REFRESH_TOKEN_KEY, refresh);
  }
};

export const clearTokens = async (): Promise<void> => {
  await storage.multiRemove([ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY]);
};

/* -------------------------------------------------------------------------- */
/* JWT Helpers                                                                */
/* -------------------------------------------------------------------------- */

export const decodeToken = (token: string): TokenPayload | null => {
  if (!token) return null;

  try {
    return jwtDecode<TokenPayload>(token);
  } catch (error) {
    console.error("Unable to decode JWT:", error);
    return null;
  }
};

export const isTokenValid = (token: string): boolean => {
  const decoded = decodeToken(token);
  if (!decoded?.exp) return false;
  
  // Add 30-second buffer to avoid edge cases
  return decoded.exp * 1000 > Date.now() + 30_000;
};

export const isTokenExpired = (token: string): boolean => {
  return !isTokenValid(token);
};

export const getTokenExpiry = (token: string): Date | null => {
  const decoded = decodeToken(token);
  if (!decoded?.exp) return null;
  return new Date(decoded.exp * 1000);
};

export const getTokenRemainingTime = (token: string): number => {
  const decoded = decodeToken(token);
  if (!decoded?.exp) return 0;
  return decoded.exp * 1000 - Date.now();
};

export const getUserIdFromToken = (token: string): number | null => {
  const decoded = decodeToken(token);
  if (decoded?.user_id != null) return decoded.user_id;
  return decoded?.sub != null ? parseInt(decoded.sub, 10) : null;
};

/* -------------------------------------------------------------------------- */
/* Axios Instances                                                            */
/* -------------------------------------------------------------------------- */

/**
 * Main authenticated API client.
 * This is the client your React Native application should normally use.
 */
export const clientApi = axios.create({
  baseURL: API_BASE,
  timeout: 30_000,
  headers: {
    Accept: "application/json",
    "Content-Type": "application/json",
  },
});

/**
 * Authentication client.
 *
 * IMPORTANT:
 * This client intentionally has NO response interceptor.
 * Authentication endpoints must not participate in the automatic refresh.
 */
export const authApi = axios.create({
  baseURL: API_BASE,
  timeout: 30_000,
  headers: {
    Accept: "application/json",
    "Content-Type": "application/json",
  },
});

/**
 * Backward-compatible alias.
 */
export const api: AxiosInstance = clientApi;

/* -------------------------------------------------------------------------- */
/* Authentication Events                                                      */
/* -------------------------------------------------------------------------- */

type SessionExpiredListener = (error?: ApiError) => void;
type TokenRefreshedListener = (newToken: string) => void;

const sessionExpiredListeners = new Set<SessionExpiredListener>();
const tokenRefreshedListeners = new Set<TokenRefreshedListener>();

export const onSessionExpired = (
  listener: SessionExpiredListener
): (() => void) => {
  sessionExpiredListeners.add(listener);
  return () => sessionExpiredListeners.delete(listener);
};

export const onTokenRefreshed = (
  listener: TokenRefreshedListener
): (() => void) => {
  tokenRefreshedListeners.add(listener);
  return () => tokenRefreshedListeners.delete(listener);
};

const notifySessionExpired = (error?: ApiError): void => {
  sessionExpiredListeners.forEach((listener) => {
    try {
      listener(error);
    } catch (error) {
      console.error("Session expired listener error:", error);
    }
  });
};

const notifyTokenRefreshed = (newToken: string): void => {
  tokenRefreshedListeners.forEach((listener) => {
    try {
      listener(newToken);
    } catch (error) {
      console.error("Token refreshed listener error:", error);
    }
  });
};

/* -------------------------------------------------------------------------- */
/* Refresh Mechanism                                                          */
/* -------------------------------------------------------------------------- */

let refreshPromise: Promise<string> | null = null;
let lastRefreshAttempt = 0;
const MIN_REFRESH_INTERVAL = 1000; // 1 second minimum between refresh attempts

/**
 * Refresh the access token.
 */
export const refreshAccessToken = async (): Promise<string> => {
  // Prevent multiple concurrent refresh requests
  if (refreshPromise) {
    return refreshPromise;
  }

  // Prevent rapid successive refresh attempts
  const now = Date.now();
  if (now - lastRefreshAttempt < MIN_REFRESH_INTERVAL) {
    await new Promise((resolve) => setTimeout(resolve, MIN_REFRESH_INTERVAL));
  }
  lastRefreshAttempt = now;

  const refreshToken = await getRefreshToken();

  if (!refreshToken) {
    const error = { detail: "No refresh token available" };
    notifySessionExpired(error);
    throw new Error("No refresh token available.");
  }

  refreshPromise = authApi
    .post<RefreshResponse>("/auth/refresh/", {
      refresh: refreshToken,
    })
    .then(async ({ data }) => {
      if (!data.access) {
        throw new Error("Refresh response did not contain an access token.");
      }

      // Support refresh-token rotation
      await setTokens(data.access, data.refresh ?? refreshToken);

      notifyTokenRefreshed(data.access);

      return data.access;
    })
    .catch(async (error: AxiosError<ApiError>) => {
      // Refresh token is invalid/expired
      if (error.response?.status === 401) {
        await clearTokens();
        notifySessionExpired(error.response?.data);
      }

      throw error;
    })
    .finally(() => {
      refreshPromise = null;
    });

  return refreshPromise;
};

/**
 * Check if a refresh is currently in progress.
 */
export const isRefreshing = (): boolean => {
  return refreshPromise !== null;
};

/* -------------------------------------------------------------------------- */
/* Request Interceptor                                                        */
/* -------------------------------------------------------------------------- */

clientApi.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    // Always get the latest token from storage
    const token = await getAccessToken();

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Let Axios handle FormData content-type
    if (config.data instanceof FormData) {
      delete config.headers["Content-Type"];
    } else if (!config.headers["Content-Type"]) {
      config.headers["Content-Type"] = "application/json";
    }

    return config;
  },
  (error) => Promise.reject(error)
);

/* -------------------------------------------------------------------------- */
/* Authentication Endpoint Detection                                          */
/* -------------------------------------------------------------------------- */

const isAuthenticationEndpoint = (url?: string): boolean => {
  if (!url) return false;

  const authEndpoints = [
    "/auth/login/",
    "/auth/register/",
    "/auth/refresh/",
    "/auth/logout/",
    "/auth/password/reset/",
    "/auth/password/change/",
    "/auth/account/deactivate/",
    "/auth/profile/",
  ];

  return authEndpoints.some((endpoint) => url.includes(endpoint));
};

/* -------------------------------------------------------------------------- */
/* Response Interceptor                                                       */
/* -------------------------------------------------------------------------- */

clientApi.interceptors.response.use(
  (response) => response,

  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config as RetryableRequestConfig | undefined;

    if (!originalRequest) {
      return Promise.reject(error);
    }

    const status = error.response?.status;

    // Only handle 401 responses
    if (status !== 401) {
      return Promise.reject(error);
    }

    // Never refresh authentication endpoints
    if (isAuthenticationEndpoint(originalRequest.url)) {
      return Promise.reject(error);
    }

    // Prevent infinite retry loop
    if (originalRequest._retry) {
      return Promise.reject(error);
    }

    // Prevent multiple refresh attempts for the same request
    if (originalRequest._refreshAttempted) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;
    originalRequest._refreshAttempted = true;

    try {
      const newAccessToken = await refreshAccessToken();

      // Update the request with the new token
      if (!originalRequest.headers) {
        originalRequest.headers = {};
      }
      originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;

      // Retry the original request
      return clientApi(originalRequest);
    } catch (refreshError) {
      // refreshAccessToken handles clearing tokens and notifying listeners
      return Promise.reject(refreshError);
    }
  }
);

/* -------------------------------------------------------------------------- */
/* Enhanced Token Utilities                                                   */
/* -------------------------------------------------------------------------- */

/**
 * Returns the currently stored access token and verifies it's still valid.
 */
export const getValidAccessToken = async (): Promise<string | null> => {
  const token = await getAccessToken();
  if (!token) return null;
  return isTokenValid(token) ? token : null;
};

/**
 * Returns true when there's a usable authenticated session.
 */
export const hasStoredSession = async (): Promise<boolean> => {
  const [accessToken, refreshToken] = await Promise.all([
    getAccessToken(),
    getRefreshToken(),
  ]);
  return !!(accessToken || refreshToken);
};

/**
 * Returns the user ID from the current token.
 */
export const getCurrentUserId = async (): Promise<number | null> => {
  const token = await getAccessToken();
  if (!token) return null;
  return getUserIdFromToken(token);
};

/**
 * Preemptively refresh the token if it's about to expire.
 * Call this before making important requests.
 */
export const ensureValidToken = async (): Promise<string | null> => {
  const token = await getAccessToken();
  
  if (!token) return null;
  
  const remaining = getTokenRemainingTime(token);
  const REFRESH_BUFFER = 5 * 60 * 1000; // 5 minutes
  
  if (remaining < REFRESH_BUFFER && remaining > 0) {
    try {
      return await refreshAccessToken();
    } catch (error) {
      console.error("Preemptive token refresh failed:", error);
      return token; // Return existing token, will fail with 401 if expired
    }
  }
  
  return isTokenValid(token) ? token : null;
};