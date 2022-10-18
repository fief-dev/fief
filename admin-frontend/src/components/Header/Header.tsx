import { Dispatch, MouseEvent } from 'react';
import { Bars3Icon } from '@heroicons/react/20/solid';

import WorkspaceSwitcher from '../WorkspaceSwitcher/WorkspaceSwitcher';
import UserMenu from '../UserMenu/UserMenu';

interface HeaderProps {
  sidebarOpen: boolean;
  setSidebarOpen: Dispatch<boolean>;
}

const Header: React.FunctionComponent<React.PropsWithChildren<HeaderProps>> = ({ sidebarOpen, setSidebarOpen }) => {

  const onBurgerButtonClick = (e: MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setSidebarOpen(!sidebarOpen);
  }

  return (
    <header className="sticky top-0 bg-white border-b border-slate-200 z-10">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 -mb-px">


          <div className="flex">

            <button
              className="text-slate-500 hover:text-slate-600 lg:hidden"
              aria-controls="sidebar"
              aria-expanded={sidebarOpen}
              onClick={onBurgerButtonClick}
            >
              <span className="sr-only">Open sidebar</span>
              <Bars3Icon className="w-6 h-6 fill-current" />
            </button>

          </div>

          <div className="flex items-center space-x-3">
            <WorkspaceSwitcher />
            <hr className="w-px h-6 bg-slate-200 mx-3" />
            <UserMenu />
          </div>

        </div>
      </div>
    </header>
  );
};

export default Header;
