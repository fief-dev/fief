import { TenantReadPublic } from './tenant';

export interface AuthorizationParameters {
  response_type: 'code';
  client_id: string;
  redirect_uri: string;
  scope: string[] | null;
  state: string | null;
}

export interface AuthorizeResponse {
  parameters: AuthorizationParameters;
  tenant: TenantReadPublic;
}

export interface LoginRequest extends AuthorizationParameters {
  username: string;
  password: string;
}

export interface LoginResponse {
  redirect_uri: string;
}
