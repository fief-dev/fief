import { CreatedUpdatedAt, UUIDSchema } from './generics';

export enum AvailableOAuthProvider {
  FACEBOOK = 'FACEBOOK',
  GITHUB = 'GITHUB',
  GOOGLE = 'GOOGLE',
  CUSTOM = 'CUSTOM',
}

export interface OAuthProviderCreate {
  provider: AvailableOAuthProvider;
  client_id: string;
  client_secret: string;
  name: string | null;
  authorize_endpoint: string | null;
  access_token_endpoint: string | null;
  refresh_token_endpoint: string | null;
  revoke_token_endpoint: string | null;
}

export interface OAuthProviderUpdate {
  client_id?: string;
  client_secret?: string;
  name?: string | null;
  authorize_endpoint?: string | null;
  access_token_endpoint?: string | null;
  refresh_token_endpoint?: string | null;
  revoke_token_endpoint?: string | null;
}

interface BaseOAUTHProvider extends UUIDSchema, CreatedUpdatedAt {
  provider: AvailableOAuthProvider;
  client_id: string;
  client_secret: string;
  name: string | null;
  authorize_endpoint: string | null;
  access_token_endpoint: string | null;
  refresh_token_endpoint: string | null;
  revoke_token_endpoint: string | null;
}

export interface OAuthProvider extends BaseOAUTHProvider { }
