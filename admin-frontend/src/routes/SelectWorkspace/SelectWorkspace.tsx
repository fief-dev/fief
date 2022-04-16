import { useTranslation } from 'react-i18next';
import { ArrowRightIcon, PlusIcon } from '@heroicons/react/solid';

import { ReactComponent as FiefLogo } from '../../images/logos/fief-logo-red.svg';
import { useWorkspacesCache } from '../../hooks/workspace';
import { Link } from 'react-router-dom';

const SelectWorkspace: React.FunctionComponent = () => {
  const { t } = useTranslation('workspaces');
  const [workspaces] = useWorkspacesCache();

  return (
    <main className="bg-white">

      <div className="fixed bottom-0 right-0 hidden md:block w-1/4 -z-1">
        <img src={`${process.env.PUBLIC_URL}/illustrations/castle.svg`} alt="Fief Castle" />
      </div>

      <div className="relative flex bg-fixed bg-repeat-x bg-bottom" style={{ backgroundImage: `url(${process.env.PUBLIC_URL}/illustrations/grass.svg)` }}>
        <div className="w-full">
          <div className="min-h-screen h-full flex flex-col after:flex-1">

            <div className="flex-1">
              <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
                <FiefLogo className="w-[60px]" />
              </div>
            </div>

            <div className="px-4 py-8">
              <div className="max-w-md mx-auto">
                <h1 className="text-3xl text-slate-800 font-bold mb-6">{t('select.title')}</h1>
                <form>
                  <div className="space-y-3 mb-8">
                    {workspaces.map((workspace) =>
                      <a key={workspace.id} className="relative block cursor-pointer" href={`${window.location.protocol}//${workspace.domain}/admin/`}>
                        <div className="flex items-center justify-between bg-white text-sm font-medium text-slate-800 p-4 rounded border border-slate-200 hover:border-slate-300 shadow-sm duration-150 ease-in-out">
                          <span>{workspace.name}</span>
                          <ArrowRightIcon width={16} height={16} className="fill-current" />
                        </div>
                      </a>
                    )}
                    <Link to="/create-workspace" className="relative block cursor-pointer">
                      <div className="flex items-center justify-between bg-white text-sm font-medium text-slate-800 p-4 rounded border border-slate-200 hover:border-slate-300 shadow-sm duration-150 ease-in-out">
                        <span>{t('select.create')}</span>
                        <PlusIcon width={16} height={16} className="fill-current" />
                      </div>
                    </Link>
                  </div>
                </form>
              </div>
            </div>

          </div>
        </div>
      </div>
    </main>
  );
};

export default SelectWorkspace;
