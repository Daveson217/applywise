import api from "@/lib/api";
import type {
  LoginRequest,
  RegisterRequest,
  RegisterResponse,
  TokenPair,
  User,
  UserProfile,
} from "@/types/auth";

export const authApi = {
  register: (data: RegisterRequest) =>
    api.post<RegisterResponse>("/auth/register/", data),

  login: (data: LoginRequest) =>
    api.post<TokenPair>("/auth/login/", data),

  refreshToken: (refresh: string) =>
    api.post<{ access: string; refresh?: string }>("/auth/token/refresh/", {
      refresh,
    }),

  getMe: () => api.get<User>("/users/me/"),

  updateMe: (
    data: Partial<Omit<User, "profile">> & { profile?: Partial<UserProfile> }
  ) => api.patch<User>("/users/me/", data),

  requestPasswordReset: (email: string) =>
    api.post<{ message: string }>("/auth/password/reset-request/", { email }),

  confirmPasswordReset: (token: string, new_password: string) =>
    api.post<{ message: string }>("/auth/password/reset-confirm/", {
      token,
      new_password,
    }),

  changePassword: (
    current_password: string,
    new_password: string,
    current_refresh?: string
  ) =>
    api.post<{ message: string }>("/auth/password/change/", {
      current_password,
      new_password,
      current_refresh,
    }),
};
