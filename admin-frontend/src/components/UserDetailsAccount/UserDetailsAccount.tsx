import { useCallback, useEffect, useState } from 'react';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { useAPI, useAPIErrorHandler } from '../../hooks/api';
import { useUserFieldsDefaultValues } from '../../hooks/user-field';
import * as schemas from '../../schemas';
import { cleanUserRequestData } from '../../services/user';
import ClipboardButton from '../ClipboardButton/ClipboardButton';
import CreateUserAccessTokenModal from '../CreateUserAccessTokenModal/CreateUserAccessTokenModal';
import DateTime from '../DateTime/DateTime';
import ErrorAlert from '../ErrorAlert/ErrorAlert';
import LoadingButton from '../LoadingButton/LoadingButton';
import UserForm from '../UserForm/UserForm';

interface UserDetailsAccountProps {
  user: schemas.user.User;
  onUpdated?: (client: schemas.user.User) => void;
}

const UserDetailsAccount: React.FunctionComponent<React.PropsWithChildren<UserDetailsAccountProps>> = ({ user, onUpdated: _onUpdated }) => {
  const { t } = useTranslation(['users']);
  const api = useAPI();
  const userFieldsDefaultValues = useUserFieldsDefaultValues();

  const form = useForm<schemas.user.UserUpdate>({ defaultValues: { ...user, fields: { ...userFieldsDefaultValues, ...user.fields } } });
  const { handleSubmit, reset, setError } = form;

  useEffect(() => {
    reset({ ...user, fields: { ...userFieldsDefaultValues, ...user.fields } });
  }, [reset, user, userFieldsDefaultValues]);

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const handleAPIError = useAPIErrorHandler(setErrorMessage, setError);

  const onUpdated = useCallback((user: schemas.user.User) => {
    if (_onUpdated) {
      _onUpdated(user);
    };
  }, [_onUpdated]);

  const onSubmit: SubmitHandler<schemas.user.UserUpdate> = useCallback(async (data) => {
    setLoading(true);
    try {
      const { data: updatedUser } = await api.updateUser(user.id, cleanUserRequestData<schemas.user.UserUpdate>(data));
      onUpdated(updatedUser);
      reset(updatedUser);
    } catch (err) {
      handleAPIError(err);
    } finally {
      setLoading(false);
    }
  }, [user, api, onUpdated, reset, handleAPIError]);

  const [createAccessTokenModalOpen, setCreateAccessTokenModalOpen] = useState(false);

  return (
    <>
      <div className="mt-6">
        <ul>
          <li className="flex items-center justify-between py-3 border-b border-slate-200">
            <div className="text-sm whitespace-nowrap">{t('details.tenant')}</div>
            <div className="text-sm font-medium text-slate-800 ml-2 truncate">{user.tenant.name}</div>
          </li>
          <li className="flex items-center justify-between py-3 border-b border-slate-200">
            <div className="text-sm whitespace-nowrap">{t('details.id')}</div>
            <div className="text-sm font-medium text-slate-800 ml-2 truncate">{user.id}</div>
            <ClipboardButton text={user.id} />
          </li>
          <li className="flex items-center justify-between py-3 border-b border-slate-200">
            <div className="text-sm whitespace-nowrap">{t('details.created_at')}</div>
            <div className="text-sm font-medium text-slate-800 ml-2 truncate"><DateTime datetime={user.created_at} displayTime /></div>
          </li>
          <li className="flex items-center justify-between py-3 border-b border-slate-200">
            <div className="text-sm whitespace-nowrap">{t('details.updated_at')}</div>
            <div className="text-sm font-medium text-slate-800 ml-2 truncate"><DateTime datetime={user.updated_at} displayTime /></div>
          </li>
          <li className="flex items-center justify-between py-3 border-b border-slate-200">
            <button
              type="button"
              className="btn w-full btn bg-primary-500 hover:bg-primary-600 text-white"
              onClick={() => setCreateAccessTokenModalOpen(true)}
            >
              {t('details.create_access_token')}
            </button>
            <CreateUserAccessTokenModal open={createAccessTokenModalOpen} user={user} onClose={() => setCreateAccessTokenModalOpen(false)} />
          </li>
        </ul>
      </div>
      <div className="mt-6">
        <FormProvider {...form}>
          <form onSubmit={handleSubmit(onSubmit)}>
            <div className="space-y-4">
              {errorMessage && <ErrorAlert message={t(`common:api_errors.${errorMessage}`)} />}
              <UserForm update={true} />
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
    </>
  );
};

export default UserDetailsAccount;
