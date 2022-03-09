import { Fragment } from 'react';
import { Link } from 'react-router-dom';
import { Menu, Transition } from '@headlessui/react'


import { useCurrentUser } from '../../hooks/user';
import UserAvatar from '../UserAvatar/UserAvatar';

interface UserMenuProps {
}

const UserMenu: React.FunctionComponent<UserMenuProps> = () => {
  const user = useCurrentUser();

  return (
    <Menu as="div" className="relative inline-block text-left">
      <div>
        <Menu.Button className="inline-flex justify-center items-center group">
          <div className="flex items-center truncate">
            <UserAvatar user={user} />
          </div>
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
          <div className="px-1 py-1">
            <Menu.Item>
              {() => (
                <div
                  className="flex flex-col rounded w-full px-2 py-2 text-sm"
                >
                  <div className="font-medium text-slate-800">{user.email}</div>
                </div>
              )}
            </Menu.Item>
          </div>
          <div className="px-1 py-1">
            <Menu.Item>
              {({ active }) => (
                <Link
                  to="/signout"
                  className={`
                    flex flex-col rounded w-full px-2 py-2 text-sm
                    ${active ? 'bg-slate-100' : ''}
                    `}
                >
                  Sign Out
                </Link>
              )}
            </Menu.Item>
          </div>
        </Menu.Items>
      </Transition>
    </Menu >
  );
};

export default UserMenu;
