import * as adminAPIKey from './admin-api-key';
import * as client from './client';
import * as emailTemplate from './email-template';
import * as oauthAccount from './oauth-account';
import * as oauthProvider from './oauth-provider';
import * as permission from './permission';
import * as role from './role';
import * as tenant from './tenant';
import * as user from './user';
import * as userField from './user-field';
import * as userPermission from './user-permission';
import * as userRole from './user-role';
import * as workspace from './workspace';

export {
  adminAPIKey,
  client,
  emailTemplate,
  oauthAccount,
  oauthProvider,
  permission,
  role,
  tenant,
  user,
  userField,
  userPermission,
  userRole,
  workspace,
};

export type { PaginatedResults, PaginationParameters, ScopesForm } from './generics';
