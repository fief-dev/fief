import { TrashIcon } from '@heroicons/react/20/solid';
import { FormEvent, useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { useAPI, useAPIErrorHandler } from '../../hooks/api';
import * as schemas from '../../schemas';
import ErrorAlert from '../ErrorAlert/ErrorAlert';
import LoadingButton from '../LoadingButton/LoadingButton';
import PermissionCombobox from '../PermissionCombobox/PermissionCombobox';

interface UserDetailsPermissionsProps {
  user: schemas.user.User;
}

const UserDetailsPermissions: React.FunctionComponent<React.PropsWithChildren<UserDetailsPermissionsProps>> = ({ user }) => {
  const { t } = useTranslation(['users']);
  const api = useAPI();

  const [userPermissions, setUserPermissions] = useState<schemas.userPermission.UserPermission[]>([]);
  const loadUserPermissions = useCallback(async () => {
    const { data: permissions } = await api.listUserPermissions(user.id, { limit: 100, ordering: 'from_role_id,created_at' });
    setUserPermissions(permissions.results);
  }, [api, user]);

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const handleAPIError = useAPIErrorHandler(setErrorMessage);

  const [permissionsToAdd, setPermissionsToAdd] = useState<string[]>([]);
  const addPermissions = useCallback(async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    try {
      for (const permissionId of permissionsToAdd) {
        await api.createUserPermission(user.id, { id: permissionId });
      }
      loadUserPermissions();
      setPermissionsToAdd([]);
    } catch (err) {
      handleAPIError(err);
    } finally {
      setLoading(false);
    }
  }, [api, user, handleAPIError, permissionsToAdd, loadUserPermissions]);

  const deletePermission = useCallback(async (permissionId: string) => {
    try {
      await api.deleteUserPermission(user.id, permissionId);
      loadUserPermissions();
    } catch (err) {
      handleAPIError(err);
    } finally {
      setLoading(false);
    }
  }, [api, user, handleAPIError, loadUserPermissions]);

  useEffect(() => {
    loadUserPermissions();
  }, [loadUserPermissions]);

  return (
    <>
      <form onSubmit={(e) => addPermissions(e)} className="space-y-4">
        {errorMessage && <ErrorAlert message={t(`common:api_errors.${errorMessage}`)} />}
        <div>
          <PermissionCombobox value={permissionsToAdd} onChange={(value) => setPermissionsToAdd(value)} />
        </div>
        <div className="flex justify-end">
          <LoadingButton
            loading={loading}
            type="submit"
            className="btn bg-primary-500 hover:bg-primary-600 text-white"
          >
            {t('details.permissions.add')}
          </LoadingButton>
        </div>
      </form>
      <table className="table-fixed w-full">
        <thead className="text-xs uppercase text-slate-400">
          <tr className="flex flex-wrap md:table-row md:flex-no-wrap">
            <th className="w-full block md:w-auto md:table-cell py-2 font-semibold text-left">{t('details.permissions.codename')}</th>
            <th className="w-full block md:w-auto md:table-cell py-2 font-semibold text-left">{t('details.permissions.from_role')}</th>
            <th className="w-full block md:w-auto md:table-cell py-2 font-semibold text-left"></th>
          </tr>
        </thead>
        <tbody className="text-sm">
          {userPermissions.length === 0 &&
            <tr className="flex flex-wrap md:table-row md:flex-no-wrap border-b border-slate-200 py-2 md:py-0 bg-slate-100">
              <td colSpan={3} className="text-center">{t('details.permissions.no_permission')}</td>
            </tr>
          }
          {userPermissions.map((userPermission) =>
            <tr
              key={userPermission.permission_id}
              className={`flex flex-wrap md:table-row md:flex-no-wrap border-b border-slate-200 py-2 md:py-0 ${userPermission.from_role !== null ? 'italic' : ''}`}
            >
              <td className="w-full block md:w-auto md:table-cell py-0.5 md:py-2">{userPermission.permission.codename}</td>
              <td className="w-full block md:w-auto md:table-cell py-0.5 md:py-2">{userPermission.from_role ? userPermission.from_role.name : '—'}</td>
              <td className="w-full block md:w-auto md:table-cell py-0.5 md:py-2 text-right">
                {userPermission.from_role_id === null &&
                  <button type="button" onClick={() => deletePermission(userPermission.permission_id)}>
                    <TrashIcon width={16} height={16} className="fill-current" />
                  </button>
                }
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </>
  );
};

export default UserDetailsPermissions;
