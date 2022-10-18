import { Dispatch, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { NavLink, useLocation } from 'react-router-dom';
import { ArrowLeftIcon } from '@heroicons/react/20/solid';

import { ReactComponent as AppsIcon } from '../../images/icons/apps.svg';
import { ReactComponent as ClientsIcon } from '../../images/icons/clients.svg';
import { ReactComponent as DashboardIcon } from '../../images/icons/dashboard.svg';
import { ReactComponent as KeyIcon } from '../../images/icons/key.svg';
import { ReactComponent as LockIcon } from '../../images/icons/lock.svg';
import { ReactComponent as TagIcon } from '../../images/icons/tag.svg';
import { ReactComponent as TenantsIcon } from '../../images/icons/tenants.svg';
import { ReactComponent as UsersIcon } from '../../images/icons/users.svg';
import { ReactComponent as FiefLogo } from '../../images/logos/fief-logo-red.svg';
import SidebarItemGroup from '../SidebarItemGroup/SidebarItemGroup';

interface SidebarProps {
  open: boolean;
  setOpen: Dispatch<boolean>;
}

const Sidebar: React.FunctionComponent<React.PropsWithChildren<SidebarProps>> = ({ open, setOpen }) => {
  const { t } = useTranslation('common');
  const { pathname } = useLocation();

  const sidebar = useRef<HTMLDivElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);

  // Outside click
  useEffect(() => {
    const clickHandler = ({ target }: MouseEvent) => {
      if (!target || !sidebar.current || !closeButton.current) return;
      if (!open || sidebar.current.contains(target as Node) || closeButton.current.contains(target as Node)) return;
      setOpen(false);
    };
    document.addEventListener('click', clickHandler);
    return () => document.removeEventListener('click', clickHandler);
  });

  // Esc key
  useEffect(() => {
    const keyHandler = ({ code }: KeyboardEvent) => {
      if (!open || code !== 'Escape') return;
      setOpen(false);
    };
    document.addEventListener('keydown', keyHandler);
    return () => document.removeEventListener('keydown', keyHandler);
  });

  return (
    <div>
      <div className={`fixed inset-0 bg-slate-900 bg-opacity-30 z-20 lg:hidden lg:z-auto transition-opacity duration-200 ${open ? 'opacity-100' : 'opacity-0 pointer-events-none'}`} aria-hidden="true"></div>

      <div
        id="sidebar"
        ref={sidebar}
        className={`flex flex-col absolute z-20 left-0 top-0 lg:static lg:left-auto lg:top-auto lg:translate-x-0 transform h-screen overflow-y-scroll lg:overflow-y-auto no-scrollbar w-64 lg:w-20 lg:sidebar-expanded:!w-64 2xl:!w-64 shrink-0 bg-slate-800 p-4 transition-all duration-200 ease-in-out ${open ? 'translate-x-0' : '-translate-x-64'}`}
      >

        <div className="flex justify-between lg:justify-center mb-10 pr-3 sm:px-2">

          <button
            ref={closeButton}
            className="lg:hidden text-slate-500 hover:text-slate-400"
            onClick={() => setOpen(false)}
            aria-controls="sidebar"
            aria-expanded={open}
          >
            <span className="sr-only">{t('sidebar.close')}</span>
            <ArrowLeftIcon className="w-6 h-6 fill-current" />
          </button>

          <NavLink end to="/" className="block">
            <FiefLogo className="w-[60px]" />
          </NavLink>
        </div>

        <div className="space-y-8">
          <div>
            <ul className="">
              <li className={`px-3 py-2 rounded-sm mb-0.5 last:mb-0 ${pathname === '/' && 'bg-slate-900'}`}>
                <NavLink end to="/" className={`block text-slate-200 hover:text-white truncate transition duration-150 ${pathname === '/' && 'hover:text-slate-200'}`}>
                  <div className="flex items-center">
                    <DashboardIcon className="shrink-0 h-6 w-6" />
                    <span className="text-sm font-medium ml-3 lg:opacity-0 lg:sidebar-expanded:opacity-100 2xl:opacity-100 duration-200">{t('sidebar.dashboard')}</span>
                  </div>
                </NavLink>
              </li>
              <li className={`px-3 py-2 rounded-sm mb-0.5 last:mb-0 ${pathname === '/tenants' && 'bg-slate-900'}`}>
                <NavLink end to="/tenants" className={`block text-slate-200 hover:text-white truncate transition duration-150 ${pathname === '/tenants' && 'hover:text-slate-200'}`}>
                  <div className="flex items-center">
                    <TenantsIcon className="shrink-0 h-6 w-6" />
                    <span className="text-sm font-medium ml-3 lg:opacity-0 lg:sidebar-expanded:opacity-100 2xl:opacity-100 duration-200">{t('sidebar.tenants')}</span>
                  </div>
                </NavLink>
              </li>
              <li className={`px-3 py-2 rounded-sm mb-0.5 last:mb-0 ${pathname === '/clients' && 'bg-slate-900'}`}>
                <NavLink end to="/clients" className={`block text-slate-200 hover:text-white truncate transition duration-150 ${pathname === '/clients' && 'hover:text-slate-200'}`}>
                  <div className="flex items-center">
                    <ClientsIcon className="shrink-0 h-6 w-6" />
                    <span className="text-sm font-medium ml-3 lg:opacity-0 lg:sidebar-expanded:opacity-100 2xl:opacity-100 duration-200">{t('sidebar.clients')}</span>
                  </div>
                </NavLink>
              </li>
              <li className={`px-3 py-2 rounded-sm mb-0.5 last:mb-0 ${pathname === '/oauth-providers' && 'bg-slate-900'}`}>
                <NavLink end to="/oauth-providers" className={`block text-slate-200 hover:text-white truncate transition duration-150 ${pathname === '/oauth-providers' && 'hover:text-slate-200'}`}>
                  <div className="flex items-center">
                    <AppsIcon className="shrink-0 h-6 w-6" />
                    <span className="text-sm font-medium ml-3 lg:opacity-0 lg:sidebar-expanded:opacity-100 2xl:opacity-100 duration-200">{t('sidebar.oauth_providers')}</span>
                  </div>
                </NavLink>
              </li>
              <li className={`px-3 py-2 rounded-sm mb-0.5 last:mb-0 ${pathname === '/users' && 'bg-slate-900'}`}>
                <NavLink end to="/users" className={`block text-slate-200 hover:text-white truncate transition duration-150 ${pathname === '/users' && 'hover:text-slate-200'}`}>
                  <div className="flex items-center">
                    <UsersIcon className="shrink-0 h-6 w-6" />
                    <span className="text-sm font-medium ml-3 lg:opacity-0 lg:sidebar-expanded:opacity-100 2xl:opacity-100 duration-200">{t('sidebar.users')}</span>
                  </div>
                </NavLink>
              </li>
              <li className={`px-3 py-2 rounded-sm mb-0.5 last:mb-0 ${pathname === '/user-fields' && 'bg-slate-900'}`}>
                <NavLink end to="/user-fields" className={`block text-slate-200 hover:text-white truncate transition duration-150 ${pathname === '/user-fields' && 'hover:text-slate-200'}`}>
                  <div className="flex items-center">
                    <TagIcon className="shrink-0 h-6 w-6" />
                    <span className="text-sm font-medium ml-3 lg:opacity-0 lg:sidebar-expanded:opacity-100 2xl:opacity-100 duration-200">{t('sidebar.user-fields')}</span>
                  </div>
                </NavLink>
              </li>
              <SidebarItemGroup
                title={t('sidebar.rbac')}
                icon={<LockIcon className="className: 'shrink-0 h-6 w-6" />}
                items={[
                  { title: t('sidebar.permissions'), href: '/permissions'},
                  { title: t('sidebar.roles'), href: '/roles'},
                ]}
                pathname={pathname}
              />
              <li className={`px-3 py-2 rounded-sm mb-0.5 last:mb-0 ${pathname === '/api-keys' && 'bg-slate-900'}`}>
                <NavLink end to="/api-keys" className={`block text-slate-200 hover:text-white truncate transition duration-150 ${pathname === '/api-keys' && 'hover:text-slate-200'}`}>
                  <div className="flex items-center">
                    <KeyIcon className="shrink-0 h-6 w-6" />
                    <span className="text-sm font-medium ml-3 lg:opacity-0 lg:sidebar-expanded:opacity-100 2xl:opacity-100 duration-200">{t('sidebar.api_keys')}</span>
                  </div>
                </NavLink>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div >
  );
};

export default Sidebar;
