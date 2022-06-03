import { useCallback, useState } from 'react';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { useAPI, useAPIErrorHandler } from '../../hooks/api';
import * as schemas from '../../schemas';
import LoadingButton from '../LoadingButton/LoadingButton';
import RoleForm from '../RoleForm/RoleForm';
import ErrorAlert from '../ErrorAlert/ErrorAlert';
import DeleteModal from '../DeleteModal/DeleteModal';

interface RoleDetailsProps {
  role: schemas.role.Role;
  onUpdated?: (role: schemas.role.Role) => void;
  onDeleted?: () => void;
}

const RoleDetails: React.FunctionComponent<React.PropsWithChildren<RoleDetailsProps>> = ({ role, onUpdated, onDeleted: _onDeleted }) => {
  const { t } = useTranslation(['roles']);
  const api = useAPI();

  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const onDeleted = useCallback(() => {
    setShowDeleteModal(false);
    if (_onDeleted) {
      _onDeleted();
    };
  }, [_onDeleted]);

  const form = useForm<schemas.role.RoleUpdate>({ defaultValues: { ...role, permissions: role.permissions.map(({ id }) => id) } });
  const { handleSubmit, setError, reset } = form;

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const handleAPIError = useAPIErrorHandler(setErrorMessage, setError);

  const onSubmit: SubmitHandler<schemas.role.RoleUpdate> = useCallback(async (data) => {
    setLoading(true);
    setErrorMessage(undefined);
    try {
      const { data: updatedRole } = await api.updateRole(role.id, data);
      if (onUpdated) {
        onUpdated(updatedRole);
        reset({ ...updatedRole, permissions: updatedRole.permissions.map(({ id }) => id) });
      }
    } catch (err) {
      handleAPIError(err);
    } finally {
      setLoading(false);
    }
  }, [api, role, onUpdated, handleAPIError, reset]);

  return (
    <>
      <div className="text-slate-800 font-semibold text-center mb-6">{role.name}</div>
      <div className="pb-6 border-b border-slate-200">
        <FormProvider {...form}>
          <form onSubmit={handleSubmit(onSubmit)}>
            <div className="space-y-4">
              {errorMessage && <ErrorAlert message={t(`common:api_errors.${errorMessage}`)} />}
              <RoleForm update role={role} />
              <LoadingButton
                loading={loading}
                type="submit"
                className="btn w-full border-slate-200 hover:border-slate-300"
              >
                {t('details.submit')}
              </LoadingButton>
            </div>
          </form>
        </FormProvider>
      </div>
      <div className="mt-6">
        <button
          type="button"
          className="btn w-full bg-red-500 hover:bg-red-600 text-white"
          onClick={() => setShowDeleteModal(true)}
        >
          {t('details.delete')}
        </button>
      </div>
      <DeleteModal
          objectId={role.id}
          method="deleteRole"
          title={t('delete.title', { name: role.name })}
          notice={t('delete.notice')}
          open={showDeleteModal}
          onClose={() => setShowDeleteModal(false)}
          onDeleted={onDeleted}
        />
    </>
  );
};

export default RoleDetails;
