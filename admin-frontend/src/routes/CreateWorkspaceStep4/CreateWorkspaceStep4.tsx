import { useCallback, useContext, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

import ErrorAlert from '../../components/ErrorAlert/ErrorAlert';
import LoadingButton from '../../components/LoadingButton/LoadingButton';
import OnboardingLayout from '../../components/OnboardingLayout/OnboardingLayout';
import CreateWorkspaceContext from '../../contexts/create-workspace';
import { useAPI, useAPIErrorHandler } from '../../hooks/api';
import * as schemas from '../../schemas';

const CreateWorkspaceStep4: React.FunctionComponent = () => {
  const { t } = useTranslation('workspaces');
  const api = useAPI();

  const [createWorkspace] = useContext(CreateWorkspaceContext);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const handleAPIError = useAPIErrorHandler(setErrorMessage);

  const onSubmit: React.FormEventHandler<HTMLFormElement> = useCallback(async (event) => {
    event.preventDefault();
    setLoading(true);
    try {
      const { data: workspace } = await api.createWorkspace(createWorkspace as schemas.workspace.WorkspaceCreate);
      window.location.href = `${window.location.protocol}//${workspace.domain}/admin/`;
    } catch (err) {
      handleAPIError(err);
    } finally {
      setLoading(false);
    }
  }, [createWorkspace, api, handleAPIError]);

  return (
    <OnboardingLayout active={4}>
      <h1 className="text-3xl text-slate-800 font-bold mb-6">{t('create.step4_title')}</h1>
      <form onSubmit={onSubmit}>
        <div className="space-y-4 mb-8">
          {errorMessage && <ErrorAlert message={t(`common:api_errors.${errorMessage}`)} />}
        </div>
        <div className="flex items-center justify-between">
          <Link className="text-sm underline hover:no-underline" to="../step3">&lt;- {t('create.back')}</Link>
          <LoadingButton loading={loading} type="submit" className="btn bg-primary-500 hover:bg-primary-600 text-white ml-auto">{t('create.create_workspace')} -&gt;</LoadingButton>
        </div>
      </form>
    </OnboardingLayout>
  );
};

export default CreateWorkspaceStep4;
