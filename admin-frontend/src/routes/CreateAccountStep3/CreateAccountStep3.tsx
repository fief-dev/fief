import { useCallback, useContext } from 'react';
import { SubmitHandler, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';

import FormErrorMessage from '../../components/FormErrorMessage/FormErrorMessage';
import OnboardingLayout from '../../components/OnboardingLayout/OnboardingLayout';
import CreateAccountContext from '../../contexts/create-account';
import { useFieldRequiredErrorMessage } from '../../hooks/errors';
import * as schemas from '../../schemas';

const CreateAccountStep3: React.FunctionComponent = () => {
  const { t } = useTranslation('accounts');
  const navigate = useNavigate();

  const [createAccount, setCreateAccount] = useContext(CreateAccountContext);
  const { register, handleSubmit, formState: { errors } } = useForm<schemas.account.AccountCreate>({ defaultValues: createAccount });
  const fieldRequiredErrorMessage = useFieldRequiredErrorMessage();

  const onSubmit: SubmitHandler<schemas.account.AccountCreate> = useCallback((data) => {
    setCreateAccount({
      ...createAccount,
      ...data,
    });
    navigate('/create-account/step4');
  }, [createAccount, setCreateAccount, navigate]);

  return (
    <OnboardingLayout active={3}>
      <h1 className="text-3xl text-slate-800 font-bold">{t('create_account.step3_title')}</h1>
      <div className="text-xs mb-6">{t('create_account.database_credentials_security_notice')}</div>
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="space-y-4 mb-8">
          <div>
            <label className="block text-sm font-medium mb-1" htmlFor="database_type">{t('create_account.database_type')}</label>
            <select
              id="database_type"
              className="form-select w-full"
              {...register('database_type', { required: fieldRequiredErrorMessage })}
            >
              {Object.values(schemas.account.DatabaseType).map((type) =>
                <option key={type} value={type}>{t(`database_type.${type}`)}</option>
              )}
            </select>
            <FormErrorMessage errors={errors} name="database_type" />
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium mb-1" htmlFor="database_host">{t('create_account.database_host')}</label>
              <input
                id="database_host"
                className="form-input w-full"
                type="text"
                {...register('database_host', { required: fieldRequiredErrorMessage })}
              />
              <FormErrorMessage errors={errors} name="database_host" />
            </div>
            <div className="col-span-1">
              <label className="block text-sm font-medium mb-1" htmlFor="database_port">{t('create_account.database_port')}</label>
              <input
                id="database_port"
                className="form-input w-full"
                type="number"
                {...register('database_port', { required: fieldRequiredErrorMessage })}
              />
              <FormErrorMessage errors={errors} name="database_port" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1" htmlFor="database_username">{t('create_account.database_username')}</label>
            <input
              id="database_username"
              className="form-input w-full"
              type="text"
              {...register('database_username', { required: fieldRequiredErrorMessage })}
            />
            <FormErrorMessage errors={errors} name="database_username" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1" htmlFor="database_password">{t('create_account.database_password')}</label>
            <input
              id="database_password"
              className="form-input w-full"
              type="password"
              autoComplete="off"
              {...register('database_password', { required: fieldRequiredErrorMessage })}
            />
            <FormErrorMessage errors={errors} name="database_password" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1" htmlFor="database_name">{t('create_account.database_name')}</label>
            <input
              id="database_name"
              className="form-input w-full"
              type="text"
              {...register('database_name', { required: fieldRequiredErrorMessage })}
            />
            <FormErrorMessage errors={errors} name="database_name" />
          </div>
        </div>
        <div className="flex items-center justify-between">
          <Link className="text-sm underline hover:no-underline" to="../step2">&lt;- {t('create_account.back')}</Link>
          <button type="submit" className="btn bg-primary-500 hover:bg-primary-600 text-white ml-auto">{t('create_account.next')} -&gt;</button>
        </div>
      </form>
    </OnboardingLayout>
  );
};

export default CreateAccountStep3;
