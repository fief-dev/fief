import { useCallback } from 'react';
import { SubmitHandler, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';

import OnboardingLayout from '../../components/OnboardingLayout/OnboardingLayout';

import { ReactComponent as CloudIcon } from '../../images/icons/cloud.svg';
import { ReactComponent as CogwheelIcon } from '../../images/icons/cogwheel.svg';


const CreateWorkspaceStep2: React.FunctionComponent = () => {
  const { t } = useTranslation('workspaces');
  const navigate = useNavigate();

  const { register, handleSubmit } = useForm<{ database: 'cloud' | 'custom' }>({ defaultValues: { database: 'cloud' } });

  const onSubmit: SubmitHandler<{ database: 'cloud' | 'custom' }> = useCallback(({ database }) => {
    if (database === 'cloud') {
      navigate('/create-workspace/step4');
    } else {
      navigate('/create-workspace/step3');
    }
  }, [navigate]);

  return (
    <OnboardingLayout active={2}>
      <h1 className="text-3xl text-slate-800 font-bold mb-6">{t('create.step2_title')}</h1>
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="sm:flex space-y-3 sm:space-y-0 sm:space-x-4 mb-8">
          <label className="flex-1 relative block cursor-pointer">
            <input
              type="radio"
              className="peer sr-only"
              value='cloud'
              {...register('database')}
            />
            <div className="h-full text-center bg-white px-4 py-6 rounded border border-slate-200 hover:border-slate-300 shadow-sm duration-150 ease-in-out">
              <CloudIcon className="inline-flex w-10 h-10 shrink-0 text-primary fill-current mb-2" />
              <div className="font-medium text-slate-800 mb-1">{t('create.cloud_database')}</div>
              <div className="text-sm">{t('create.cloud_database_details')}</div>
            </div>
            <div className="absolute inset-0 border-2 border-transparent peer-checked:border-primary-400 rounded pointer-events-none" aria-hidden="true"></div>
          </label>
          <label className="flex-1 relative block cursor-pointer">
            <input
              type="radio"
              className="peer sr-only"
              value='custom'
              {...register('database')}
            />
            <div className="h-full text-center bg-white px-4 py-6 rounded border border-slate-200 hover:border-slate-300 shadow-sm duration-150 ease-in-out">
              <CogwheelIcon className="inline-flex w-10 h-10 shrink-0 text-primary fill-current mb-2" />
              <div className="font-medium text-slate-800 mb-1">{t('create.custom_database')}</div>
              <div className="text-sm">{t('create.custom_database_details')}</div>
            </div>
            <div className="absolute inset-0 border-2 border-transparent peer-checked:border-primary-400 rounded pointer-events-none" aria-hidden="true"></div>
          </label>
        </div>
        <div className="flex items-center justify-between">
          <Link className="text-sm underline hover:no-underline" to="../step1">&lt;- {t('create.back')}</Link>
          <button type="submit" className="btn bg-primary-500 hover:bg-primary-600 text-white ml-auto">{t('create.next')} -&gt;</button>
        </div>
      </form>
    </OnboardingLayout>
  );
};

export default CreateWorkspaceStep2;
