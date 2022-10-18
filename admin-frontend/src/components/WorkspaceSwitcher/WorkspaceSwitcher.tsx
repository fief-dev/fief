import { Fragment, useCallback, useContext } from 'react';
import { Menu, Transition } from '@headlessui/react'
import { ChevronDownIcon, PlusIcon } from '@heroicons/react/20/solid';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

import WorkspaceContext from '../../contexts/workspace';
import { useWorkspacesCache } from '../../hooks/workspace';
import * as schemas from '../../schemas';

interface WorkspaceSwitcherProps {
}

const WorkspaceSwitcher: React.FunctionComponent<React.PropsWithChildren<WorkspaceSwitcherProps>> = () => {
  const { t } = useTranslation(['common']);
  const [workspaces] = useWorkspacesCache();
  const [workspace, setWorkspace] = useContext(WorkspaceContext);
  const navigate = useNavigate();

  const switchWorkspace = useCallback((workspace: schemas.workspace.WorkspacePublic) => {
    setWorkspace(workspace);
    window.location.host = workspace.domain;
  }, [setWorkspace]);

  const createWorkspace = useCallback(() => {
    navigate('/create-workspace');
  }, [navigate]);

  return (
    <Menu as="div" className="relative inline-block text-left">
      <div>
        <Menu.Button className="inline-flex justify-center items-center group">
          <span className="truncate text-sm font-medium group-hover:text-slate-800 mr-1">{workspace?.name}</span>
          <ChevronDownIcon width={16} height={16} className="fill-slate-400" />
        </Menu.Button>
      </div>
      <Transition
        as={Fragment}
        enter="transition ease-out duration-100"
        enterFrom="transform opacity-0 scale-95"
        enterTo="transform opacity-100 scale-100"
        leave="transition ease-in duration-75"
        leaveFrom="transform opacity-100 scale-100"
        leaveTo="transform opacity-0 scale-95"
      >
        <Menu.Items className="absolute right-0 w-56 mt-2 origin-top-right bg-white divide-y divide-gray-100 rounded shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
          {workspaces.map((workspace) =>
            <div key={workspace.id} className="px-1 py-1">
              <Menu.Item>
                {({ active }) => (
                  <button
                    type="button"
                    className={`
                      flex flex-col rounded w-full px-2 py-2 text-sm
                      ${active ? 'bg-slate-100' : ''}
                      `}
                    onClick={() => switchWorkspace(workspace)}
                  >
                    <div className="font-medium text-slate-800">{workspace.name}</div>
                    <div className="text-xs text-slate-500">{workspace.domain}</div>
                  </button>
                )}
              </Menu.Item>
            </div>
          )}
          <div className="px-1 py-1">
            <Menu.Item>
              {({ active }) => (
                <button
                  type="button"
                  className={`
                      flex flex-col rounded w-full px-2 py-2 text-sm
                      ${active ? 'bg-slate-100' : ''}
                      `}
                  onClick={() => createWorkspace()}
                >
                  <div className="flex justify-between items-center w-full font-medium text-slate-800">
                    {t('workspace_switcher.create')}
                    <PlusIcon width="16" height="16" />
                  </div>
                </button>
              )}
            </Menu.Item>
          </div>
        </Menu.Items>
      </Transition>
    </Menu>
  );
};

export default WorkspaceSwitcher;
