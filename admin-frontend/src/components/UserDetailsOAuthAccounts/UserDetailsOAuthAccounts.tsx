import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { useAPI } from '../../hooks/api';
import * as schemas from '../../schemas';
import DateTime from '../DateTime/DateTime';

interface UserDetailsOAuthAccountsProps {
  user: schemas.user.User;
}

const UserDetailsOAuthAccounts: React.FunctionComponent<React.PropsWithChildren<UserDetailsOAuthAccountsProps>> = ({ user }) => {
  const { t } = useTranslation(['users', 'oauth-providers']);
  const api = useAPI();

  const [oauthAccounts, setOAuthAccounts] = useState<schemas.oauthAccount.OAuthAccount[]>([]);
  const loadUserPermissions = useCallback(async () => {
    const { data: oauthAccounts } = await api.listUserOAuthAccounts(user.id, { limit: 100, ordering: 'created_at' });
    setOAuthAccounts(oauthAccounts.results);
  }, [api, user]);

  useEffect(() => {
    loadUserPermissions();
  }, [loadUserPermissions]);

  return (
    <>
      <table className="table-fixed w-full">
        <thead className="text-xs uppercase text-slate-400">
          <tr className="flex flex-wrap md:table-row md:flex-no-wrap">
            <th className="w-full block md:w-auto md:table-cell py-2 font-semibold text-left">{t('details.oauth_accounts.provider')}</th>
            <th className="w-full block md:w-auto md:table-cell py-2 font-semibold text-right">{t('details.oauth_accounts.updated_at')}</th>
          </tr>
        </thead>
        <tbody className="text-sm">
          {oauthAccounts.length === 0 &&
            <tr className="flex flex-wrap md:table-row md:flex-no-wrap border-b border-slate-200 py-2 md:py-0 bg-slate-100">
              <td colSpan={3} className="text-center">{t('details.oauth_accounts.no_oauth_account')}</td>
            </tr>
          }
          {oauthAccounts.map((oauthAccount) =>
            <tr
              key={oauthAccount.id}
              className="flex flex-wrap md:table-row md:flex-no-wrap border-b border-slate-200 py-2 md:py-0"
            >
              <td className="w-full block md:w-auto md:table-cell py-0.5 md:py-2">{t(`oauth-providers:available_oauth_provider.${oauthAccount.oauth_provider.provider}`)}</td>
              <td className="w-full block md:w-auto md:table-cell py-0.5 md:py-2 text-right">
                <DateTime datetime={oauthAccount.updated_at} />
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </>
  );
};

export default UserDetailsOAuthAccounts;
