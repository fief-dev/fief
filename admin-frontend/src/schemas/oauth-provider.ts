import { CreatedUpdatedAt, ScopesForm, UUIDSchema } from './generics';

export enum AvailableOAuthProvider {
  DISCORD = 'DISCORD',
  FACEBOOK = 'FACEBOOK',
  GITHUB = 'GITHUB',
  GOOGLE = 'GOOGLE',
  LINKEDIN = 'LINKEDIN',
  MICROSOFT = 'MICROSOFT',
  REDDIT = 'REDDIT',
  OPENID = 'OPENID',
}

export interface OAuthProviderCreateBase {
  provider: AvailableOAuthProvider;
  client_id: string;
  client_secret: string;
  name: string | null;
  openid_configuration_endpoint: string | null;
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
  openid_configuration_endpoint?: string | null;
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
  openid_configuration_endpoint: string | null;
}

export interface OAuthProvider extends BaseOAUTHProvider { }
