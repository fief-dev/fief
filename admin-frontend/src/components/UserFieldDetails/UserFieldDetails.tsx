import { useCallback, useEffect, useState } from 'react';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { useAPI, useAPIErrorHandler } from '../../hooks/api';
import * as schemas from '../../schemas';
import DeleteModal from '../DeleteModal/DeleteModal';
import ErrorAlert from '../ErrorAlert/ErrorAlert';
import LoadingButton from '../LoadingButton/LoadingButton';
import UserFieldForm from '../UserFieldForm/UserFieldForm';

interface UserFieldDetailsProps {
  userField: schemas.userField.UserField;
  onUpdated?: (client: schemas.userField.UserField) => void;
  onDeleted?: () => void;
}

const UserFieldDetails: React.FunctionComponent<UserFieldDetailsProps> = ({ userField, onUpdated: _onUpdated, onDeleted: _onDeleted }) => {
  const { t } = useTranslation(['user-fields']);
  const api = useAPI();

  const getSafeDefaultValue = (userField: schemas.userField.UserField): schemas.userField.UserField => {
    return {
      ...userField,
      configuration: {
        ...userField.configuration,
        choices: userField.configuration.choices || undefined,
      }
    };
  };

  const form = useForm<schemas.userField.UserFieldUpdate>({ defaultValues: getSafeDefaultValue(userField) });
  const { handleSubmit, reset, setError } = form;

  useEffect(() => {
    reset(getSafeDefaultValue(userField));
  }, [reset, userField]);

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const handleAPIError = useAPIErrorHandler(setErrorMessage, setError);

  const onUpdated = useCallback((userField: schemas.userField.UserField) => {
    if (_onUpdated) {
      _onUpdated(userField);
    };
  }, [_onUpdated]);

  const onSubmit: SubmitHandler<schemas.userField.UserFieldUpdate> = useCallback(async (data) => {
    setLoading(true);
    try {
      const { data: updatedUserField } = await api.updateUserField(userField.id, data);
      onUpdated(updatedUserField);
      reset(getSafeDefaultValue(updatedUserField));
    } catch (err) {
      handleAPIError(err);
    } finally {
      setLoading(false);
    }
  }, [userField, api, onUpdated, reset, handleAPIError]);

  const [showDeleteModal, setShowDeleteModal] = useState(false);

  const onDeleted = useCallback(() => {
    if (_onDeleted) {
      _onDeleted();
    };
  }, [_onDeleted]);

  return (
    <>
      <div className="text-slate-800 font-semibold text-center mb-6">{userField.name}</div>
      <div className="pb-6 border-b border-slate-200">
        <FormProvider {...form}>
          <form onSubmit={handleSubmit(onSubmit)}>
            <div className="space-y-4">
              {errorMessage && <ErrorAlert message={t(`common:api_errors.${errorMessage}`)} />}
              <UserFieldForm update={true} />
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
        objectId={userField.id}
        method="deleteUserField"
        title={t('delete.title', { name: userField.name })}
        notice={t('delete.notice')}
        open={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onDeleted={onDeleted}
      />
    </>
  );
};

export default UserFieldDetails;
