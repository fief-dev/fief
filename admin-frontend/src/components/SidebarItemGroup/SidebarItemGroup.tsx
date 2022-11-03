import { ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/20/solid';
import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';

interface SubItem {
  title: string;
  href: string;
}

interface SidebarItemGroupProps {
  title: string;
  icon: React.ReactElement;
  items: SubItem[];
  pathname: string;
}

const SidebarItemGroup: React.FunctionComponent<React.PropsWithChildren<SidebarItemGroupProps>> = ({ title, icon, items, pathname }) => {
  const itemsActive = items.map(({ href }) => pathname.startsWith(href));
  const active = itemsActive.some((itemActive) => itemActive === true);
  const [open, setOpen] = useState(active);

  const onOpen = () => {
    setOpen(!open);
  };

  return (
    <li className={`px-3 py-2 rounded-sm mb-0.5 last:mb-0 ${active && 'bg-slate-900'}`}>
      <button
        type="button"
        className={`block w-full text-slate-200 hover:text-white truncate transition duration-150 ${open && 'hover:text-slate-200'}`}
        onClick={() => onOpen()}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            {icon}
            <span className="text-sm font-medium ml-3 lg:opacity-0 lg:sidebar-expanded:opacity-100 2xl:opacity-100 duration-200">{title}</span>
          </div>
          <div>
            {!open && <ChevronDownIcon width={16} height={16} className="fill-slate-400" />}
            {open && <ChevronUpIcon width={16} height={16} className="fill-slate-400" />}
          </div>
        </div>
      </button>
      {open &&
        <div className="lg:hidden lg:sidebar-expanded:block 2xl:block">
          <ul className="pl-9 mt-1">
            {items.map((item, i) =>
              <li key={item.href} className="mb-1 last:mb-0">
                <NavLink end to={item.href} className={`block hover:text-slate-200 transition duration-150 truncate ${itemsActive[i] ? 'text-primary-500' : 'text-slate-400'}`}>
                  <span className="text-sm font-medium lg:opacity-0 lg:sidebar-expanded:opacity-100 2xl:opacity-100 duration-200">{item.title}</span>
                </NavLink>
              </li>
            )}
          </ul>
        </div>
      }
    </li>
  );
};

export default SidebarItemGroup;
