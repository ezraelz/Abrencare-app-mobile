
export interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isSuperuser: boolean;
  isAdmin: boolean;
  accessToken: string | null;
  refreshToken: string | null;
}

export interface AuthContext {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isSuperuser: boolean;
  login: (username: string, password: string, rememberMe?: boolean) => Promise<void>;
  logout: () => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  refreshSession: () => Promise<void>;
  updateUser: (user: User) => void;
  hasRole: (roles: string | string[]) => boolean;
  accessToken: string | null;
}

export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  first_name: string;
  last_name: string;
  sex: "M" | "F" | "Other" | null;
  phone: number;
  age: number | null;
  date_of_birth: string | null;
  contact: string | null;
  address: string | null;
  bio: string | null;
  role: string;
  role_name: string;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  profile_image: string | null;
  created_at: string;
  last_seen: string | null;
  permissions: string[];
  deactivated_at: string;
  deactivation_reason: string;
  updated_at: string;
}

export interface UserCreateData {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  role: string;
  is_agreed_to_terms: boolean;
}

export interface UserUpdateData {
  username?: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  sex?: "M" | "F" | "Other";
  age?: number;
  date_of_birth?: string;
  contact?: string;
  address?: string;
  bio?: string;
  role?: string;
  is_active?: boolean;
  is_staff?: boolean;
  is_superuser?: boolean;
  profile_image?: File | null;
  password?: string;
  confirm_password?: string;
}

export interface UseUserDataReturn {
  users: User[];
  user: User | null;
  total: number;
  isLoading: boolean;
  error: string | null;
  fetchUsers: () => Promise<void>;
  fetchUser: (id: string) => Promise<User | null>;
  createUser: (userData: UserCreateData) => Promise<User>;
  updateUser: (id: string, userData: UserUpdateData) => Promise<User>;
  deleteUser: (id: string) => Promise<void>;
  toggleUserStatus: (id: string) => Promise<User>;
  changePassword: (id: string, data: {
    current_password: string;
    new_password: string;
    confirm_password: string;
  }) => Promise<void>;
  getCurrentUser: () => Promise<User | null>;
  fetchDeactivatedUsers: () => Promise<void>;
  reactivateUser: (userId: number) => Promise<boolean>;
  permanentDeleteUser: (userId: number) => Promise<boolean>;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegistrationData {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetVerify {
  email: string;
  code: string;
}

export interface PasswordResetConfirm {
  reset_token: string;
  new_password: string;
}

export interface ChangePasswordData {
  current_password: string;
  new_password: string;
}