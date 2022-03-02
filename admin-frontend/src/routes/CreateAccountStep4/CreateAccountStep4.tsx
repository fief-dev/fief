import { useCallback, useContext, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

import ErrorAlert from '../../components/ErrorAlert/ErrorAlert';
import LoadingButton from '../../components/LoadingButton/LoadingButton';
import OnboardingLayout from '../../components/OnboardingLayout/OnboardingLayout';
import CreateAccountContext from '../../contexts/create-account';
import { useAPI } from '../../hooks/api';
import * as schemas from '../../schemas';
import { handleAPIError } from '../../services/api';

const CreateAccountStep4: React.FunctionComponent = () => {
  const { t } = useTranslation('accounts');
  const api = useAPI();

  const [createAccount] = useContext(CreateAccountContext);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | undefined>();

  const onSubmit: React.FormEventHandler<HTMLFormElement> = useCallback(async (event) => {
    event.preventDefault();
    setLoading(true);
    try {
      const { data: account } = await api.createAccount(createAccount as schemas.account.AccountCreate);
      window.location.hostname = account.domain;
    } catch (err) {
      setErrorMessage(handleAPIError(err));
    } finally {
      setLoading(false);
    }
  }, [createAccount, api]);

  return (
    <OnboardingLayout active={4}>
      <h1 className="text-3xl text-slate-800 font-bold mb-6">{t('create_account.step4_title')}</h1>
      <form onSubmit={onSubmit}>
        <div className="space-y-4 mb-8">
          {errorMessage && <ErrorAlert message={t(`common:api_errors.${errorMessage}`)} />}
        </div>
        <div className="flex items-center justify-between">
          <Link className="text-sm underline hover:no-underline" to="../step3">&lt;- {t('create_account.back')}</Link>
          <LoadingButton loading={loading} type="submit" className="btn bg-primary-500 hover:bg-primary-600 text-white ml-auto">{t('create_account.create_account')} -&gt;</LoadingButton>
        </div>
      </form>
    </OnboardingLayout>
  );
};

export default CreateAccountStep4;
