import { useTranslation } from 'react-i18next';
import Layout from '../../components/Layout/Layout';

const Dashboard: React.FunctionComponent<React.PropsWithChildren<unknown>> = () => {
  const { t } = useTranslation(['dashboard']);

  return (
    <Layout>
      <div className="relative bg-slate-200 p-4 sm:p-6 rounded-sm overflow-hidden mb-8 ">
        <div className="relative">
          <h1 className="text-2xl md:text-3xl text-slate-800 font-bold mb-1">{t('greet')}</h1>
          <p className="mb-4">{t('message')}</p>
          <a
            className="btn bg-primary-500 hover:bg-primary-600 text-white"
            href="https://docs.fief.dev"
            target="_blank"
            rel="noopener noreferrer"
          >
            {t('documentation')}
          </a>
          <a
            className="btn bg-white border-slate-200 hover:border-slate-300 text-slate-600 ml-2"
            href="https://github.com/fief-dev/fief/discussions"
            target="_blank"
            rel="noopener noreferrer"
          >
            {t('ask')}
          </a>
        </div>
      </div>
    </Layout>
  );
};

export default Dashboard;
