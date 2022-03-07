import { Dispatch } from 'react';

import AccountSwitcher from '../AccountSwitcher/AccountSwitcher';
import UserMenu from '../UserMenu/UserMenu';

interface HeaderProps {
  sidebarOpen: boolean;
  setSidebarOpen: Dispatch<boolean>;
}

const Header: React.FunctionComponent<HeaderProps> = ({ sidebarOpen, setSidebarOpen }) => {
  return (
    <header className="sticky top-0 bg-white border-b border-slate-200 z-10">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 -mb-px">


          <div className="flex">

            <button
              className="text-slate-500 hover:text-slate-600 lg:hidden"
              aria-controls="sidebar"
              aria-expanded={sidebarOpen}
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              <span className="sr-only">Open sidebar</span>
              <svg className="w-6 h-6 fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <rect x="4" y="5" width="16" height="2" />
                <rect x="4" y="11" width="16" height="2" />
                <rect x="4" y="17" width="16" height="2" />
              </svg>
            </button>

          </div>

          <div className="flex items-center space-x-3">
            <AccountSwitcher />
            <hr className="w-px h-6 bg-slate-200 mx-3" />
            <UserMenu />
          </div>

        </div>
      </div>
    </header>
  );
};

export default Header;
