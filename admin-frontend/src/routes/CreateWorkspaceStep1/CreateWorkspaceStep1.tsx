import { useCallback, useContext } from 'react';
import { SubmitHandler, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

import FormErrorMessage from '../../components/FormErrorMessage/FormErrorMessage';
import OnboardingLayout from '../../components/OnboardingLayout/OnboardingLayout';
import CreateWorkspacesContext from '../../contexts/create-workspace';
import { useFieldRequiredErrorMessage } from '../../hooks/errors';
import * as schemas from '../../schemas';

const CreateWorkspaceStep1: React.FunctionComponent<React.PropsWithChildren<unknown>> = () => {
  const { t } = useTranslation('workspaces');
  const navigate = useNavigate();

  const [createWorkspace, setCreateWorkspace] = useContext(CreateWorkspacesContext);
  const { register, handleSubmit, formState: { errors } } = useForm<schemas.workspace.WorkspaceCreate>({ defaultValues: createWorkspace });
  const fieldRequiredErrorMessage = useFieldRequiredErrorMessage();

  const onSubmit: SubmitHandler<schemas.workspace.WorkspaceCreate> = useCallback((data) => {
    setCreateWorkspace({
      ...createWorkspace,
      ...data,
    });
    navigate('/create-workspace/step2');
  }, [createWorkspace, setCreateWorkspace, navigate]);

  return (
    <OnboardingLayout active={1}>
      <h1 className="text-3xl text-slate-800 font-bold mb-6">{t('create.step1_title')}</h1>
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="space-y-4 mb-8">
          <div>
            <label className="block text-sm font-medium mb-1" htmlFor="name">{t('create.name')}</label>
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
          <button type="submit" className="btn bg-primary-500 hover:bg-primary-600 text-white ml-auto">{t('create.next')} -&gt;</button>
        </div>
      </form>
    </OnboardingLayout>
  );
};

export default CreateWorkspaceStep1;
