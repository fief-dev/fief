import { CreatedUpdatedAt, UUIDSchema } from './generics';

export enum AvailableOAuthProvider {
  FACEBOOK = 'FACEBOOK',
  GITHUB = 'GITHUB',
  GOOGLE = 'GOOGLE',
  CUSTOM = 'CUSTOM',
}

export interface ScopesForm {
  scopes: {
    id: string;
    value: string
  }[];
}

export interface OAuthProviderCreateBase {
  provider: AvailableOAuthProvider;
  client_id: string;
  client_secret: string;
  name: string | null;
  authorize_endpoint: string | null;
  access_token_endpoint: string | null;
  refresh_token_endpoint: string | null;
  revoke_token_endpoint: string | null;
}

export interface OAuthProviderCreateForm extends OAuthProviderCreateBase, ScopesForm {
}

export interface OAuthProviderCreate extends OAuthProviderCreateBase {
  scopes: string[];
}

export interface OAuthProviderUpdateBase {
  client_id?: string;
  client_secret?: string;
  name?: string | null;
  authorize_endpoint?: string | null;
  access_token_endpoint?: string | null;
  refresh_token_endpoint?: string | null;
  revoke_token_endpoint?: string | null;
}

export interface OAuthProviderUpdateForm extends OAuthProviderUpdateBase, Partial<ScopesForm> {
}

export interface OAuthProviderUpdate extends OAuthProviderUpdateBase {
  scopes?: string[];
}

interface BaseOAUTHProvider extends UUIDSchema, CreatedUpdatedAt {
  provider: AvailableOAuthProvider;
  client_id: string;
  client_secret: string;
  scopes: string[];
  name: string | null;
  authorize_endpoint: string | null;
  access_token_endpoint: string | null;
  refresh_token_endpoint: string | null;
  revoke_token_endpoint: string | null;
}

export interface OAuthProvider extends BaseOAUTHProvider { }
