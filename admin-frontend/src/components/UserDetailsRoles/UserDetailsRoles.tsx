import { TrashIcon } from '@heroicons/react/solid';
import { FormEvent, useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { useAPI, useAPIErrorHandler } from '../../hooks/api';
import * as schemas from '../../schemas';
import ErrorAlert from '../ErrorAlert/ErrorAlert';
import LoadingButton from '../LoadingButton/LoadingButton';
import RoleCombobox from '../RoleCombobox/RoleCombobox';

interface UserDetailsRolesProps {
  user: schemas.user.User;
}

const UserDetailsRoles: React.FunctionComponent<React.PropsWithChildren<UserDetailsRolesProps>> = ({ user }) => {
  const { t } = useTranslation(['users']);
  const api = useAPI();

  const [userRoles, setUserRoles] = useState<schemas.userRole.UserRole[]>([]);
  const loadUserRoles = useCallback(async () => {
    const { data: roles } = await api.listUserRoles(user.id, { limit: 100, ordering: 'created_at' });
    setUserRoles(roles.results);
  }, [api, user]);

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const handleAPIError = useAPIErrorHandler(setErrorMessage);

  const [rolesToAdd, setRolesToAdd] = useState<string[]>([]);
  const addRoles = useCallback(async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    try {
      for (const roleId of rolesToAdd) {
        await api.createUserRole(user.id, { id: roleId });
      }
      loadUserRoles();
      setRolesToAdd([]);
    } catch (err) {
      handleAPIError(err);
    } finally {
      setLoading(false);
    }
  }, [api, user, handleAPIError, rolesToAdd, loadUserRoles]);

  const deleteRole = useCallback(async (roleId: string) => {
    try {
      await api.deleteUserRole(user.id, roleId);
      loadUserRoles();
    } catch (err) {
      handleAPIError(err);
    } finally {
      setLoading(false);
    }
  }, [api, user, handleAPIError, loadUserRoles]);

  useEffect(() => {
    loadUserRoles();
  }, [loadUserRoles]);

  return (
    <>
      <form onSubmit={(e) => addRoles(e)} className="space-y-4">
        {errorMessage && <ErrorAlert message={t(`common:api_errors.${errorMessage}`)} />}
        <div>
          <RoleCombobox value={rolesToAdd} onChange={(value) => setRolesToAdd(value)} />
        </div>
        <div className="flex justify-end">
          <LoadingButton
            loading={loading}
            type="submit"
            className="btn bg-primary-500 hover:bg-primary-600 text-white"
          >
            {t('details.roles.add')}
          </LoadingButton>
        </div>
      </form>
      <table className="table-fixed w-full">
        <thead className="text-xs uppercase text-slate-400">
          <tr className="flex flex-wrap md:table-row md:flex-no-wrap">
            <th className="w-full block md:w-auto md:table-cell py-2 font-semibold text-left">{t('details.roles.name')}</th>
            <th className="w-full block md:w-auto md:table-cell py-2 font-semibold text-left"></th>
          </tr>
        </thead>
        <tbody className="text-sm">
          {userRoles.length === 0 &&
            <tr className="flex flex-wrap md:table-row md:flex-no-wrap border-b border-slate-200 py-2 md:py-0 bg-slate-100">
              <td colSpan={2} className="text-center">{t('details.roles.no_role')}</td>
            </tr>
          }
          {userRoles.map((userRole) =>
            <tr key={userRole.role_id} className="flex flex-wrap md:table-row md:flex-no-wrap border-b border-slate-200 py-2 md:py-0">
              <td className="w-full block md:w-auto md:table-cell py-0.5 md:py-2">{userRole.role.name}</td>
              <td className="w-full block md:w-auto md:table-cell py-0.5 md:py-2 text-right">
                <button type="button" onClick={() => deleteRole(userRole.role_id)}>
                  <TrashIcon width={16} height={16} className="fill-current" />
                </button>
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </>
  );
};

export default UserDetailsRoles;
