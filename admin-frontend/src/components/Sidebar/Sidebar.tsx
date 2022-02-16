import { Dispatch, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { NavLink, useLocation } from 'react-router-dom';

import { ReactComponent as ClientsIcon } from '../../icons/clients.svg';
import { ReactComponent as DashboardIcon } from '../../icons/dashboard.svg';
import { ReactComponent as TenantsIcon } from '../../icons/tenants.svg';
import { ReactComponent as UsersIcon } from '../../icons/users.svg';

interface SidebarProps {
  open: boolean;
  setOpen: Dispatch<boolean>;
}

const Sidebar: React.FunctionComponent<SidebarProps> = ({ open, setOpen }) => {
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
      <div className={`fixed inset-0 bg-slate-900 bg-opacity-30 z-40 lg:hidden lg:z-auto transition-opacity duration-200 ${open ? 'opacity-100' : 'opacity-0 pointer-events-none'}`} aria-hidden="true"></div>

      <div
        id="sidebar"
        ref={sidebar}
        className={`flex flex-col absolute z-40 left-0 top-0 lg:static lg:left-auto lg:top-auto lg:translate-x-0 transform h-screen overflow-y-scroll lg:overflow-y-auto no-scrollbar w-64 lg:w-20 lg:sidebar-expanded:!w-64 2xl:!w-64 shrink-0 bg-slate-800 p-4 transition-all duration-200 ease-in-out ${open ? 'translate-x-0' : '-translate-x-64'}`}
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
            <svg className="w-6 h-6 fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M10.7 18.7l1.4-1.4L7.8 13H20v-2H7.8l4.3-4.3-1.4-1.4L4 12z" />
            </svg>
          </button>

          <NavLink end to="/" className="block">
            <img src="/fief-logo-red.svg" alt="Fief" width={60} />
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
              <li className={`px-3 py-2 rounded-sm mb-0.5 last:mb-0 ${pathname === '/users' && 'bg-slate-900'}`}>
                <NavLink end to="/users" className={`block text-slate-200 hover:text-white truncate transition duration-150 ${pathname === '/users' && 'hover:text-slate-200'}`}>
                  <div className="flex items-center">
                    <UsersIcon className="shrink-0 h-6 w-6" />
                    <span className="text-sm font-medium ml-3 lg:opacity-0 lg:sidebar-expanded:opacity-100 2xl:opacity-100 duration-200">{t('sidebar.users')}</span>
                  </div>
                </NavLink>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
