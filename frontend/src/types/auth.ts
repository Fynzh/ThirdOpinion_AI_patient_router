export interface AuthUser {
  id: number;
  username: string;
  email: string;
}

export interface CurrentUser extends AuthUser {
  is_staff: boolean;
  is_superuser: boolean;
}

export interface AuthResponse {
  token: string;
  user: AuthUser;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegisterPayload extends LoginPayload {
  email?: string;
}