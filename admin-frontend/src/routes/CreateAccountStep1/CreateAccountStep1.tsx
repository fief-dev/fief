import { useCallback, useContext } from 'react';
import { SubmitHandler, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

import FormErrorMessage from '../../components/FormErrorMessage/FormErrorMessage';
import OnboardingLayout from '../../components/OnboardingLayout/OnboardingLayout';
import CreateAccountContext from '../../contexts/create-account';
import { useFieldRequiredErrorMessage } from '../../hooks/errors';
import * as schemas from '../../schemas';

const CreateAccountStep1: React.FunctionComponent = () => {
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
    navigate('/create-account/step2');
  }, [createAccount, setCreateAccount, navigate]);

  return (
    <OnboardingLayout active={1}>
      <h1 className="text-3xl text-slate-800 font-bold mb-6">{t('create_account.step1_title')}</h1>
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="space-y-4 mb-8">
          <div>
            <label className="block text-sm font-medium mb-1" htmlFor="name">{t('create_account.name')}</label>
            <input
              id="name"
              className="form-input w-full"
              type="text"
              {...register('name', { required: fieldRequiredErrorMessage })}
            />
            <FormErrorMessage errors={errors} name="name" />
          </div>
        </div>
        <div className="flex items-center justify-between">
          <button type="submit" className="btn bg-primary-500 hover:bg-primary-600 text-white ml-auto">{t('create_account.next')} -&gt;</button>
        </div>
      </form>
    </OnboardingLayout>
  );
};

export default CreateAccountStep1;
