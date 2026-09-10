// hooks/useAuth.tsx

import {
  createContext,
  createElement,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { toast } from "sonner-native";

import {
  api,
  authApi,
  clearTokens,
  decodeToken,
  getAccessToken,
  getRefreshToken,
  isTokenValid,
  refreshAccessToken,
  setTokens,
  onSessionExpired,
  onTokenRefreshed,
  ensureValidToken,
} from "../services/api";

import type { AuthState, User } from "../types/authTypes";

/* -------------------------------------------------------------------------- */
/* Types                                                                      */
/* -------------------------------------------------------------------------- */

export interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;

  register: (
    email: string,
    password: string,
    username: string,
  ) => Promise<User | null>;

  refreshSession: () => Promise<string | null>;
  getCurrentUser: () => Promise<User | null>;
  ensureValidSession: () => Promise<string | null>;

  updateProfile: (data: Partial<User>) => Promise<User | null>;
  deactivateAccount: () => Promise<void>;

  changePassword: (
    currentPassword: string,
    newPassword: string
  ) => Promise<void>;

  requestPasswordReset: (email: string) => Promise<void>;
  verifyResetCode: (email: string, code: string) => Promise<{ resetToken: string }>;
  resetPassword: (resetToken: string, newPassword: string) => Promise<void>;

  updateUser: (user: User) => void;

  hasRole: (roles: string | string[]) => boolean;
  getRole: () => string | undefined;

  isSuperuser: boolean;
  isAdmin: boolean;
  isTokenExpiringSoon: boolean;
}

/* -------------------------------------------------------------------------- */
/* Constants                                                                  */
/* -------------------------------------------------------------------------- */

const TOKEN_EXPIRY_WARNING_MS = 5 * 60 * 1000; // 5 minutes

/* -------------------------------------------------------------------------- */
/* Initial State                                                              */
/* -------------------------------------------------------------------------- */

const INITIAL_STATE: AuthState = {
  user: null,
  isLoading: true,
  isAuthenticated: false,
  isSuperuser: false,
  isAdmin: false,
  accessToken: null,
  refreshToken: null,
};

/* -------------------------------------------------------------------------- */
/* Context                                                                    */
/* -------------------------------------------------------------------------- */

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/* -------------------------------------------------------------------------- */
/* Provider                                                                   */
/* -------------------------------------------------------------------------- */

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(INITIAL_STATE);
  const [isTokenExpiringSoon, setIsTokenExpiringSoon] = useState(false);
  const tokenExpiryCheckInterval = useRef<ReturnType<typeof setInterval> | null>(null);
  const isMounted = useRef<boolean>(true);

  /* ------------------------------------------------------------------------ */
  /* Lifecycle                                                                 */
  /* ------------------------------------------------------------------------ */

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
      if (tokenExpiryCheckInterval.current) {
        clearInterval(tokenExpiryCheckInterval.current);
        tokenExpiryCheckInterval.current = null;
      }
    };
  }, []);

  /* ------------------------------------------------------------------------ */
  /* Role Helpers                                                             */
  /* ------------------------------------------------------------------------ */

  const getRoleFromToken = useCallback((token: string): string | undefined => {
    const decoded = decodeToken(token);
    if (!decoded) return undefined;
    return (decoded.role as string | undefined) ?? (decoded.role_name as string | undefined);
  }, []);

  const getRoleFromUser = useCallback((user: User | null): string | undefined => {
    if (!user) return undefined;
    return (user as User & { role_name?: string }).role_name;
  }, []);

  /* ------------------------------------------------------------------------ */
  /* Build Authentication State                                               */
  /* ------------------------------------------------------------------------ */

  const buildAuthState = useCallback(
    (user: User, accessToken: string, refreshToken: string | null): AuthState => {
      const decoded = decodeToken(accessToken);
      const role = getRoleFromUser(user) ?? getRoleFromToken(accessToken);

      const isSuperuser =
        user.is_superuser === true ||
        decoded?.is_superuser === true ||
        decoded?.isSuperuser === true;

      const isAdmin = role === "admin" || isSuperuser;

      return {
        user,
        isLoading: false,
        isAuthenticated: true,
        isSuperuser,
        isAdmin,
        accessToken,
        refreshToken,
      };
    },
    [getRoleFromUser, getRoleFromToken]
  );

  /* ------------------------------------------------------------------------ */
  /* Reset Authentication State                                               */
  /* ------------------------------------------------------------------------ */

  const resetAuthState = useCallback((): void => {
    void clearTokens();
    if (tokenExpiryCheckInterval.current) {
      clearInterval(tokenExpiryCheckInterval.current);
      tokenExpiryCheckInterval.current = null;
    }
    setIsTokenExpiringSoon(false);

    if (isMounted.current) {
      setState({
        ...INITIAL_STATE,
        isLoading: false,
      });
    }
  }, []);

  /* ------------------------------------------------------------------------ */
  /* Check Token Expiry Status                                                */
  /* ------------------------------------------------------------------------ */

  const checkTokenExpiry = useCallback(async (): Promise<void> => {
    const token = await getAccessToken();
    if (!token) {
      setIsTokenExpiringSoon(false);
      return;
    }

    if (!isTokenValid(token)) {
      setIsTokenExpiringSoon(false);
      return;
    }

    const decoded = decodeToken(token);
    if (!decoded?.exp) {
      setIsTokenExpiringSoon(false);
      return;
    }

    const expiresIn = decoded.exp * 1000 - Date.now();
    const isExpiringSoon = expiresIn > 0 && expiresIn < TOKEN_EXPIRY_WARNING_MS;

    setIsTokenExpiringSoon(isExpiringSoon);

    // If expiring soon, try to refresh proactively
    if (isExpiringSoon && state.isAuthenticated) {
      try {
        await refreshSession();
      } catch (error) {
        console.warn("Proactive token refresh failed:", error);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.isAuthenticated]);

  /* ------------------------------------------------------------------------ */
  /* Start Token Expiry Monitoring                                            */
  /* ------------------------------------------------------------------------ */

  const startTokenExpiryMonitoring = useCallback((): void => {
    if (tokenExpiryCheckInterval.current) {
      clearInterval(tokenExpiryCheckInterval.current);
      tokenExpiryCheckInterval.current = null;
    }

    // Check every minute
    tokenExpiryCheckInterval.current = setInterval(() => {
      void checkTokenExpiry();
    }, 60_000);
    
    // Immediate check
    void checkTokenExpiry();
  }, [checkTokenExpiry]);

  /* ------------------------------------------------------------------------ */
  /* Current User                                                             */
  /* ------------------------------------------------------------------------ */

  const getCurrentUser = useCallback(async (): Promise<User | null> => {
    try {
      const response = await api.get<User>("/auth/profile/");
      return response.data;
    } catch (error) {
      console.error("Failed to fetch current user:", error);
      return null;
    }
  }, []);

  /* ------------------------------------------------------------------------ */
  /* Refresh Session                                                          */
  /* ------------------------------------------------------------------------ */

  const refreshSession = useCallback(async (): Promise<string | null> => {
    try {
      const refreshToken = await getRefreshToken();

      if (!refreshToken) {
        resetAuthState();
        return null;
      }

      // Attempt to get a valid token (this will refresh if needed)
      const accessToken = await refreshAccessToken();

      // Fetch the latest user data
      const user = await getCurrentUser();

      if (!user) {
        throw new Error("Unable to load user after session refresh.");
      }

      const currentRefreshToken = await getRefreshToken();

      if (isMounted.current) {
        setState(buildAuthState(user, accessToken, currentRefreshToken));
        startTokenExpiryMonitoring();
      }

      return accessToken;
    } catch (error) {
      console.error("Session refresh failed:", error);
      resetAuthState();
      return null;
    }
  }, [buildAuthState, getCurrentUser, resetAuthState, startTokenExpiryMonitoring]);

  /* ------------------------------------------------------------------------ */
  /* Ensure Valid Session                                                     */
  /* ------------------------------------------------------------------------ */

  const ensureValidSession = useCallback(async (): Promise<string | null> => {
    try {
      const token = await ensureValidToken();
      if (token) {
        // Update state if needed
        const user = await getCurrentUser();
        if (user && isMounted.current) {
          const refreshToken = await getRefreshToken();
          setState(buildAuthState(user, token, refreshToken));
        }
        return token;
      }
      return null;
    } catch (error) {
      console.error("Failed to ensure valid session:", error);
      return null;
    }
  }, [buildAuthState, getCurrentUser]);

  /* ------------------------------------------------------------------------ */
  /* Initialize Authentication                                                */
  /* ------------------------------------------------------------------------ */

  useEffect(() => {
    const initializeAuth = async (): Promise<void> => {
      try {
        const accessToken = await getAccessToken();
        const refreshToken = await getRefreshToken();

        // No session exists
        if (!accessToken && !refreshToken) {
          if (isMounted.current) {
            setState({ ...INITIAL_STATE, isLoading: false });
          }
          return;
        }

        // Existing valid access token
        if (accessToken && isTokenValid(accessToken)) {
          const user = await getCurrentUser();

          if (user && isMounted.current) {
            const currentRefreshToken = await getRefreshToken();
            setState(buildAuthState(user, accessToken, currentRefreshToken));
            startTokenExpiryMonitoring();
            return;
          }
        }

        // Access token expired → refresh
        if (refreshToken) {
          await refreshSession();
          return;
        }

        // No usable session
        if (isMounted.current) {
          resetAuthState();
        }
      } catch (error) {
        console.error("Authentication initialization failed:", error);
        if (isMounted.current) {
          resetAuthState();
        }
      }
    };

    void initializeAuth();

    // Set up session expired listener
    const unsubscribeSessionExpired = onSessionExpired(() => {
      console.warn("Authentication session expired.");
      resetAuthState();
      toast.error("Your session has expired. Please sign in again.");
    });

    // Set up token refreshed listener
    const unsubscribeTokenRefreshed = onTokenRefreshed(() => {
      // Update token expiry monitoring
      void checkTokenExpiry();
    });

    return () => {
      unsubscribeSessionExpired();
      unsubscribeTokenRefreshed();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* ------------------------------------------------------------------------ */
  /* Login                                                                    */
  /* ------------------------------------------------------------------------ */

  const login = useCallback(
    async (email: string, password: string): Promise<void> => {
      try {
        setState((prev) => ({ ...prev, isLoading: true }));

        const response = await authApi.post<{ access: string; refresh: string }>(
          "/auth/login/",
          {
            email,
            password,
          }
        );

        const { access, refresh } = response.data;

        if (!access || !refresh) {
          throw new Error("Login response did not contain authentication tokens.");
        }

        // Store tokens securely
        await setTokens(access, refresh);

        // Fetch authoritative user information
        const user = await getCurrentUser();

        if (!user) {
          throw new Error("Unable to load authenticated user.");
        }

        if (isMounted.current) {
          setState(buildAuthState(user, access, refresh));
          startTokenExpiryMonitoring();
        }

        toast.success(`Welcome back, ${user.first_name || user.email}!`);
      } catch (error: unknown) {
        console.error("Login error:", error);

        if (isMounted.current) {
          setState((prev) => ({ ...prev, isLoading: false }));
        }

        // Extract meaningful error message
        let message = "Login failed. Please try again.";

        if (error && typeof error === "object" && "response" in error) {
          const err = error as { response?: { status?: number; data?: Record<string, unknown> } };
          
          if (err.response?.status === 401) {
            message = "Invalid email or password.";
          } else if (err.response?.data?.detail) {
            message = String(err.response.data.detail);
          } else if (err.response?.data?.error) {
            const errorData = err.response.data.error;
            if (typeof errorData === "string") {
              message = errorData;
            } else if (Array.isArray(errorData)) {
              message = errorData.join("\n");
            }
          }
        }

        toast.error(message);
        throw error;
      }
    },
    [buildAuthState, getCurrentUser, startTokenExpiryMonitoring]
  );

  /* ------------------------------------------------------------------------ */
  /* Register                                                                 */
  /* ------------------------------------------------------------------------ */

  const register = useCallback(
    async (
      username: string,
      password: string,
      email: string,
    ): Promise<User | null> => {
      try {
        setState((prev) => ({ ...prev, isLoading: true }));

        const response = await api.post<{ user: User; message?: string }>(
          "/auth/register/",
          {
            username,
            password,
            email,
          }
        );

        const user = response.data?.user ?? null;

        toast.success(
          response.data?.message || "Registration successful! Please verify your email."
        );

        if (isMounted.current) {
          setState({ ...INITIAL_STATE, isLoading: false });
        }

        return user;
      } catch (error: unknown) {
        console.error("Registration error:", error);

        if (isMounted.current) {
          setState((prev) => ({ ...prev, isLoading: false }));
        }

        let message = "Registration failed. Please try again.";

        if (error && typeof error === "object" && "response" in error) {
          const err = error as { response?: { status?: number; data?: Record<string, unknown> } };
          
          if (err.response?.status === 400) {
            const data = err.response.data;
            if (data?.email) {
              const emailError = data.email;
              message = Array.isArray(emailError) ? String(emailError[0]) : String(emailError);
            } else if (data?.error) {
              const errorData = data.error;
              message = typeof errorData === "string" ? errorData : JSON.stringify(errorData);
            } else {
              message = "Please check the information you provided.";
            }
          } else if (err.response?.data?.detail) {
            message = String(err.response.data.detail);
          }
        }

        toast.error(message);
        throw error;
      }
    },
    []
  );

  /* ------------------------------------------------------------------------ */
  /* Logout                                                                   */
  /* ------------------------------------------------------------------------ */

  const logout = useCallback(async (): Promise<void> => {
    const refreshToken = await getRefreshToken();

    try {
      if (refreshToken) {
        await api.post("/auth/logout/");
      }
    } catch (error) {
      // Logout should still succeed locally even if the server request fails
      console.error("Logout API error:", error);
    } finally {
      resetAuthState();
      toast.success("Logged out successfully.");
    }
  }, [resetAuthState]);

  /* ------------------------------------------------------------------------ */
  /* Update Profile                                                           */
  /* ------------------------------------------------------------------------ */

  const updateProfile = useCallback(
    async (data: Partial<User>): Promise<User | null> => {
      try {
        const response = await api.put<User>("/auth/profile/", data);
        const updatedUser = response.data;

        if (updatedUser && isMounted.current) {
          setState((prev) => ({
            ...prev,
            user: updatedUser,
          }));
        }

        toast.success("Profile updated successfully.");
        return updatedUser;
      } catch (error: unknown) {
        console.error("Profile update error:", error);

        let message = "Failed to update profile.";

        if (error && typeof error === "object" && "response" in error) {
          const err = error as { response?: { data?: Record<string, unknown> } };
          message = String(
            err.response?.data?.detail ||
            err.response?.data?.error ||
            "Failed to update profile."
          );
        }

        toast.error(message);
        throw error;
      }
    },
    []
  );

  /* ------------------------------------------------------------------------ */
  /* Deactivate Account                                                       */
  /* ------------------------------------------------------------------------ */

  const deactivateAccount = useCallback(async (): Promise<void> => {
    try {
      await api.post("/auth/account/deactivate/");
      resetAuthState();
      toast.success("Your account has been deactivated successfully.");
    } catch (error: unknown) {
      console.error("Account deactivation error:", error);

      let message = "Failed to deactivate your account.";

      if (error && typeof error === "object" && "response" in error) {
        const err = error as { response?: { data?: Record<string, unknown> } };
        message = String(
          err.response?.data?.detail ||
          err.response?.data?.error ||
          "Failed to deactivate your account."
        );
      }

      toast.error(message);
      throw error;
    }
  }, [resetAuthState]);

  /* ------------------------------------------------------------------------ */
  /* Change Password                                                          */
  /* ------------------------------------------------------------------------ */

  const changePassword = useCallback(
    async (currentPassword: string, newPassword: string): Promise<void> => {
      try {
        await api.post("/auth/password/change/", {
          current_password: currentPassword,
          new_password: newPassword,
        });

        toast.success("Password changed successfully. Please sign in again on other devices.");
      } catch (error: unknown) {
        console.error("Password change error:", error);

        let message = "Failed to change password.";

        if (error && typeof error === "object" && "response" in error) {
          const err = error as { response?: { data?: Record<string, unknown> } };
          const data = err.response?.data;
          
          if (data?.error) {
            const errorData = data.error;
            if (typeof errorData === "string") {
              message = errorData;
            } else if (Array.isArray(errorData)) {
              message = errorData.join("\n");
            } else if (typeof errorData === "object") {
              message = Object.values(errorData).flat().join("\n");
            }
          } else if (data?.detail) {
            message = String(data.detail);
          }
        }

        toast.error(message);
        throw error;
      }
    },
    []
  );

  /* ------------------------------------------------------------------------ */
  /* Request Password Reset                                                   */
  /* ------------------------------------------------------------------------ */

  const requestPasswordReset = useCallback(
    async (email: string): Promise<void> => {
      try {
        await authApi.post("/auth/password/reset/request/", { email });
        toast.success("If the email exists, a reset code has been sent.");
      } catch (error: unknown) {
        console.error("Password reset request error:", error);
        // Always show the same message for security
        toast.success("If the email exists, a reset code has been sent.");
        // Still throw for error handling in the component
        throw error;
      }
    },
    []
  );

  /* ------------------------------------------------------------------------ */
  /* Verify Reset Code                                                        */
  /* ------------------------------------------------------------------------ */

  const verifyResetCode = useCallback(
    async (email: string, code: string): Promise<{ resetToken: string }> => {
      try {
        const response = await authApi.post<{ reset_token: string; message?: string }>(
          "/auth/password/reset/verify/",
          {
            email,
            code,
          }
        );

        const { reset_token } = response.data;

        if (!reset_token) {
          throw new Error("Reset token not returned.");
        }

        toast.success(response.data?.message || "Code verified successfully.");
        return { resetToken: reset_token };
      } catch (error: unknown) {
        console.error("Password reset verification error:", error);

        let message = "Invalid or expired verification code.";

        if (error && typeof error === "object" && "response" in error) {
          const err = error as { response?: { data?: Record<string, unknown> } };
          message = String(
            err.response?.data?.detail ||
            err.response?.data?.error ||
            "Invalid or expired verification code."
          );
        }

        toast.error(message);
        throw error;
      }
    },
    []
  );

  /* ------------------------------------------------------------------------ */
  /* Reset Password                                                           */
  /* ------------------------------------------------------------------------ */

  const resetPassword = useCallback(
    async (resetToken: string, newPassword: string): Promise<void> => {
      try {
        await authApi.post("/auth/password/reset/confirm/", {
          reset_token: resetToken,
          new_password: newPassword,
        });

        toast.success("Password reset successfully. Please sign in with your new password.");
      } catch (error: unknown) {
        console.error("Password reset error:", error);

        let message = "Failed to reset password.";

        if (error && typeof error === "object" && "response" in error) {
          const err = error as { response?: { data?: Record<string, unknown> } };
          const data = err.response?.data;
          
          if (data?.error) {
            const errorData = data.error;
            if (typeof errorData === "string") {
              message = errorData;
            } else if (Array.isArray(errorData)) {
              message = errorData.join("\n");
            }
          } else if (data?.detail) {
            message = String(data.detail);
          }
        }

        toast.error(message);
        throw error;
      }
    },
    []
  );

  /* ------------------------------------------------------------------------ */
  /* User Utilities                                                           */
  /* ------------------------------------------------------------------------ */

  const updateUser = useCallback(
    (user: User): void => {
      if (!isMounted.current) return;

      setState((prev) => {
        const role = getRoleFromUser(user) ?? (prev.accessToken ? getRoleFromToken(prev.accessToken) : undefined);

        return {
          ...prev,
          user,
          isSuperuser: user.is_superuser === true || prev.isSuperuser,
          isAdmin: role === "admin" || prev.isAdmin,
        };
      });
    },
    [getRoleFromUser, getRoleFromToken]
  );

  /* ------------------------------------------------------------------------ */
  /* Get Role                                                                 */
  /* ------------------------------------------------------------------------ */

  const getRole = useCallback((): string | undefined => {
    if (!state.user) return undefined;

    return (
      getRoleFromUser(state.user) ??
      (state.accessToken ? getRoleFromToken(state.accessToken) : undefined)
    );
  }, [state.user, state.accessToken, getRoleFromUser, getRoleFromToken]);

  /* ------------------------------------------------------------------------ */
  /* Has Role                                                                 */
  /* ------------------------------------------------------------------------ */

  const hasRole = useCallback(
    (roles: string | string[]): boolean => {
      const roleList = Array.isArray(roles) ? roles : [roles];
      const currentRole = getRole();

      if (currentRole && roleList.includes(currentRole)) {
        return true;
      }

      if (state.isSuperuser && roleList.some((role) => ["superuser", "owner"].includes(role))) {
        return true;
      }

      if (state.isAdmin && roleList.includes("admin")) {
        return true;
      }

      return false;
    },
    [getRole, state.isSuperuser, state.isAdmin]
  );

  /* ------------------------------------------------------------------------ */
  /* Context Value                                                            */
  /* ------------------------------------------------------------------------ */

  const value = useMemo<AuthContextType>(
    () => ({
      ...state,
      login,
      logout,
      register,
      refreshSession,
      getCurrentUser,
      ensureValidSession,
      updateProfile,
      deactivateAccount,
      changePassword,
      requestPasswordReset,
      verifyResetCode,
      resetPassword,
      updateUser,
      hasRole,
      getRole,
      isSuperuser: state.isSuperuser,
      isAdmin: state.isAdmin,
      isTokenExpiringSoon,
    }),
    [
      state,
      login,
      logout,
      register,
      refreshSession,
      getCurrentUser,
      ensureValidSession,
      updateProfile,
      deactivateAccount,
      changePassword,
      requestPasswordReset,
      verifyResetCode,
      resetPassword,
      updateUser,
      hasRole,
      getRole,
      isTokenExpiringSoon,
    ]
  );

  return createElement(AuthContext.Provider, { value }, children);
}

/* -------------------------------------------------------------------------- */
/* Hook                                                                       */
/* -------------------------------------------------------------------------- */

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}