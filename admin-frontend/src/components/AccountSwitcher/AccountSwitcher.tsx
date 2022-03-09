import { Fragment, useCallback, useContext } from 'react';
import { Menu, Transition } from '@headlessui/react'
import { ChevronDownIcon } from '@heroicons/react/solid';

import AccountContext from '../../contexts/account';
import { useAccountsCache } from '../../hooks/account';
import * as schemas from '../../schemas';

interface AccountSwitcherProps {
}

const AccountSwitcher: React.FunctionComponent<AccountSwitcherProps> = () => {
  const [accounts] = useAccountsCache();
  const [account, setAccount] = useContext(AccountContext);

  const switchAccount = useCallback((account: schemas.account.AccountPublic) => {
    setAccount(account);
    window.location.hostname = account.domain;
  }, [setAccount]);

  return (
    <Menu as="div" className="relative inline-block text-left">
      <div>
        <Menu.Button className="inline-flex justify-center items-center group">
          <span className="truncate text-sm font-medium group-hover:text-slate-800 mr-1">{account?.name}</span>
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
          {accounts.map((account) =>
            <div key={account.id} className="px-1 py-1">
              <Menu.Item>
                {({ active }) => (
                  <button
                    type="button"
                    className={`
                      flex flex-col rounded w-full px-2 py-2 text-sm
                      ${active ? 'bg-slate-100' : ''}
                      `}
                    onClick={() => switchAccount(account)}
                  >
                    <div className="font-medium text-slate-800">{account.name}</div>
                    <div className="text-xs text-slate-500">{account.domain}</div>
                  </button>
                )}
              </Menu.Item>
            </div>
          )}
        </Menu.Items>
      </Transition>
    </Menu>
  );
};

export default AccountSwitcher;
