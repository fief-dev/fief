import { useCallback, useEffect, useMemo, useState } from 'react';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { useAPI, useAPIErrorHandler } from '../../hooks/api';
import * as schemas from '../../schemas';
import { FIEF_INSTANCE } from '../../services/api';
import ClipboardButton from '../ClipboardButton/ClipboardButton';
import ErrorAlert from '../ErrorAlert/ErrorAlert';
import LoadingButton from '../LoadingButton/LoadingButton';
import TenantForm from '../TenantForm/TenantForm';

interface TenantDetailsProps {
  tenant: schemas.tenant.Tenant;
  onUpdated?: (client: schemas.tenant.Tenant) => void;
}

const TenantDetails: React.FunctionComponent<React.PropsWithChildren<TenantDetailsProps>> = ({ tenant, onUpdated }) => {
  const { t } = useTranslation(['tenants']);
  const api = useAPI();

  const baseURL = useMemo(() => tenant.default ? FIEF_INSTANCE : `${FIEF_INSTANCE}/${tenant.slug}`, [tenant]);

  const form = useForm<schemas.tenant.TenantUpdate>({ defaultValues: tenant });
  const { handleSubmit, reset, setError } = form;

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const handleAPIError = useAPIErrorHandler(setErrorMessage, setError);

  const onSubmit: SubmitHandler<schemas.tenant.TenantUpdate> = useCallback(async (data) => {
    setLoading(true);
    try {
      const { data: updatedTenant } = await api.updateTenant(tenant.id, data);
      if (onUpdated) {
        onUpdated(updatedTenant);
        reset(updatedTenant);
      }
    } catch (err) {
      handleAPIError(err);
    } finally {
      setLoading(false);
    }
  }, [tenant, api, onUpdated, reset, handleAPIError]);

  useEffect(() => {
    reset(tenant);
  }, [reset, tenant]);

  return (
    <>
      <div className="text-slate-800 font-semibold text-center mb-6">{tenant.name}</div>
      <div className="mt-6">
        <ul>
          <li className="flex items-center justify-between py-3 border-b border-slate-200">
            <div className="text-sm whitespace-nowrap">{t('details.base_url')}</div>
            <div className="text-sm font-medium text-slate-800 ml-2 truncate">{baseURL}</div>
            <ClipboardButton text={baseURL} />
          </li>
        </ul>
      </div>
      <div className="mt-6 pb-6 border-b border-slate-200">
        <FormProvider {...form}>
          <form onSubmit={handleSubmit(onSubmit)}>
            <div className="space-y-4">
              {errorMessage && <ErrorAlert message={t(`common:api_errors.${errorMessage}`)} />}
              <TenantForm update={true} />
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

export default TenantDetails;
