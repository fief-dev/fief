import axios, { AxiosError, AxiosInstance, AxiosResponse } from 'axios';

import * as schemas from '../schemas';

export const API_PORT = process.env.REACT_APP_API_PORT || window.location.port;
export const FIEF_INSTANCE = `${window.location.protocol}//${window.location.hostname}${API_PORT ? `:${API_PORT}` : ''}`;
const BASE_URL = `${FIEF_INSTANCE}/admin/api`;

export class APIClient {
  client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: BASE_URL,
      withCredentials: true,
    });
  }

  public static getLoginURL(): string {
    return `${BASE_URL}/auth/login?redirect_uri=${encodeURIComponent(window.location.href)}`;
  }

  public static getLogoutURL(): string {
    return `${BASE_URL}/auth/logout`;
  }

  public getOpenAPI(): Promise<AxiosResponse<Record<string, any>>> {
    return this.client.get('/openapi.json');
  }

  public getUserinfo(): Promise<AxiosResponse<schemas.user.CurrentUser>> {
    return this.client.get('/auth/userinfo');
  }

  public listWorkspaces(params: schemas.PaginationParameters = {}): Promise<AxiosResponse<schemas.PaginatedResults<schemas.workspace.WorkspacePublic>>> {
    return this.client.get('/workspaces/', { params });
  }

  public createWorkspace(data: schemas.workspace.WorkspaceCreate): Promise<AxiosResponse<schemas.workspace.WorkspacePublic>> {
    return this.client.post('/workspaces/', data);
  }

  public checkConnectionWorkspace(data: schemas.workspace.WorkspaceCheckConnection): Promise<AxiosResponse<void>> {
    return this.client.post('/workspaces/check-connection', data);
  }

  public listTenants(params: schemas.tenant.TenantListParameters = {}): Promise<AxiosResponse<schemas.PaginatedResults<schemas.tenant.Tenant>>> {
    return this.client.get('/tenants/', { params });
  }

  public createTenant(data: schemas.tenant.TenantCreate): Promise<AxiosResponse<schemas.tenant.Tenant>> {
    return this.client.post('/tenants/', data);
  }

  public listClients(params: schemas.PaginationParameters = {}): Promise<AxiosResponse<schemas.PaginatedResults<schemas.client.Client>>> {
    return this.client.get('/clients/', { params });
  }

  public createClient(data: schemas.client.ClientCreate): Promise<AxiosResponse<schemas.client.Client>> {
    return this.client.post('/clients/', data);
  }

  public updateClient(id: string, data: schemas.client.ClientUpdate): Promise<AxiosResponse<schemas.client.Client>> {
    return this.client.patch(`/clients/${id}`, data);
  }

  public createClientEncryptionKey(id: string): Promise<AxiosResponse<Record<string, string>>> {
    return this.client.post(`/clients/${id}/encryption-key`);
  }

  public listOAuthProviders(params: schemas.PaginationParameters = {}): Promise<AxiosResponse<schemas.PaginatedResults<schemas.oauthProvider.OAuthProvider>>> {
    return this.client.get('/oauth-providers/', { params });
  }

  public createOAuthProvider(data: schemas.oauthProvider.OAuthProviderCreate): Promise<AxiosResponse<schemas.oauthProvider.OAuthProvider>> {
    return this.client.post('/oauth-providers/', data);
  }

  public updateOAuthProvider(id: string, data: schemas.oauthProvider.OAuthProviderUpdate): Promise<AxiosResponse<schemas.oauthProvider.OAuthProvider>> {
    return this.client.patch(`/oauth-providers/${id}`, data);
  }

  public deleteOAuthProvider(id: string): Promise<AxiosResponse<void>> {
    return this.client.delete(`/oauth-providers/${id}`);
  }

  public listUsers(params: schemas.PaginationParameters = {}): Promise<AxiosResponse<schemas.PaginatedResults<schemas.user.User>>> {
    return this.client.get('/users/', { params });
  }

  public getUser(id: string): Promise<AxiosResponse<schemas.user.User>> {
    return this.client.get(`/users/${id}`);
  }

  public listUserPermissions(id: string, params: schemas.PaginationParameters = {}): Promise<AxiosResponse<schemas.PaginatedResults<schemas.userPermission.UserPermission>>> {
    return this.client.get(`/users/${id}/permissions`, { params });
  }

  public createUserPermission(id: string, data: schemas.userPermission.UserPermissionCreate): Promise<AxiosResponse<void>> {
    return this.client.post(`/users/${id}/permissions`, data);
  }

  public deleteUserPermission(id: string, permissionId: string): Promise<AxiosResponse<void>> {
    return this.client.delete(`/users/${id}/permissions/${permissionId}`);
  }

  public listUserRoles(id: string, params: schemas.PaginationParameters = {}): Promise<AxiosResponse<schemas.PaginatedResults<schemas.userRole.UserRole>>> {
    return this.client.get(`/users/${id}/roles`, { params });
  }

  public createUserRole(id: string, data: schemas.userRole.UserRoleCreate): Promise<AxiosResponse<void>> {
    return this.client.post(`/users/${id}/roles`, data);
  }

  public deleteUserRole(id: string, roleId: string): Promise<AxiosResponse<void>> {
    return this.client.delete(`/users/${id}/roles/${roleId}`);
  }

  public listUserOAuthAccounts(id: string, params: schemas.PaginationParameters = {}): Promise<AxiosResponse<schemas.PaginatedResults<schemas.oauthAccount.OAuthAccount>>> {
    return this.client.get(`/users/${id}/oauth-accounts`, { params });
  }

  public createUser(data: schemas.user.UserCreateInternal): Promise<AxiosResponse<schemas.user.User>> {
    return this.client.post('/users/', data);
  }

  public updateUser(id: string, data: schemas.user.UserUpdate): Promise<AxiosResponse<schemas.user.User>> {
    return this.client.patch(`/users/${id}`, data);
  }

  public listUserFields(params: schemas.PaginationParameters = {}): Promise<AxiosResponse<schemas.PaginatedResults<schemas.userField.UserField>>> {
    return this.client.get('/user-fields/', { params });
  }

  public createUserField(data: schemas.userField.UserFieldCreate): Promise<AxiosResponse<schemas.userField.UserField>> {
    return this.client.post('/user-fields/', data);
  }

  public updateUserField(id: string, data: schemas.userField.UserFieldUpdate): Promise<AxiosResponse<schemas.userField.UserField>> {
    return this.client.patch(`/user-fields/${id}`, data);
  }

  public deleteUserField(id: string): Promise<AxiosResponse<void>> {
    return this.client.delete(`/user-fields/${id}`);
  }

  public listPermissions(params: schemas.permission.PermissionListParameters = {}): Promise<AxiosResponse<schemas.PaginatedResults<schemas.permission.Permission>>> {
    return this.client.get('/permissions/', { params });
  }

  public createPermission(data: schemas.permission.PermissionCreate): Promise<AxiosResponse<schemas.permission.Permission>> {
    return this.client.post('/permissions/', data);
  }

  public updatePermission(id: string, data: schemas.permission.PermissionUpdate): Promise<AxiosResponse<schemas.permission.Permission>> {
    return this.client.patch(`/permissions/${id}`, data);
  }

  public deletePermission(id: string): Promise<AxiosResponse<void>> {
    return this.client.delete(`/permissions/${id}`);
  }

  public listRoles(params: schemas.role.RoleListParameters = {}): Promise<AxiosResponse<schemas.PaginatedResults<schemas.role.Role>>> {
    return this.client.get('/roles/', { params });
  }

  public createRole(data: schemas.role.RoleCreate): Promise<AxiosResponse<schemas.role.Role>> {
    return this.client.post('/roles/', data);
  }

  public updateRole(id: string, data: schemas.role.RoleUpdate): Promise<AxiosResponse<schemas.role.Role>> {
    return this.client.patch(`/roles/${id}`, data);
  }

  public deleteRole(id: string): Promise<AxiosResponse<void>> {
    return this.client.delete(`/roles/${id}`);
  }

  public listAPIKeys(params: schemas.PaginationParameters = {}): Promise<AxiosResponse<schemas.PaginatedResults<schemas.adminAPIKey.AdminAPIKey>>> {
    return this.client.get('/api-keys/', { params });
  }

  public createAPIKey(data: schemas.adminAPIKey.AdminAPIKeyCreate): Promise<AxiosResponse<schemas.adminAPIKey.AdminAPIKeyCreateResponse>> {
    return this.client.post('/api-keys/', data);
  }

  public deleteAPIKey(id: string): Promise<AxiosResponse<void>> {
    return this.client.delete(`/api-keys/${id}`);
  }
}

export const isAxiosException = (e: unknown): e is AxiosError<{ detail: any }> => e instanceof AxiosError;

interface FieldError {
  loc: string[];
  msg: string;
  type: string;
}

export const handleAPIError = (err: unknown): [string | undefined, FieldError[]] => {
  if (isAxiosException(err)) {
    const response = err.response;
    if (response) {
      if (response.status === 422) {
        return [undefined, response.data.detail];
      } else if (response.status === 400) {
        return [response.data.detail, []];
      } else {
        return ['UNKNOWN_ERROR', []];
      }
    }
  }
  throw err;
};
