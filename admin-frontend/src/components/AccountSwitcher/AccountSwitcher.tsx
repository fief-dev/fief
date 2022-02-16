import { useCallback, useContext, useRef } from 'react';

import AccountContext from '../../contexts/account';
import { useAccountsCache } from '../../hooks/account';
import { useToggle } from '../../hooks/toggle';
import * as schemas from '../../schemas';

interface AccountSwitcherProps {
}

const AccountSwitcher: React.FunctionComponent<AccountSwitcherProps> = () => {
  const accounts = useAccountsCache();
  const [account, setAccount] = useContext(AccountContext);

  const trigger = useRef<HTMLButtonElement>(null);
  const dropdown = useRef<HTMLDivElement>(null);
  const [dropdownOpen, setDropdownOpen] = useToggle(trigger, dropdown, false);

  const switchAccount = useCallback((account: schemas.account.AccountPublic) => {
    setAccount(account);
    setDropdownOpen(false);
    window.location.reload();
  }, [setAccount, setDropdownOpen]);

  return (
    <div className="relative inline-flex">
      <button
        ref={trigger}
        className="inline-flex justify-center items-center group"
        aria-haspopup="true"
        onClick={() => setDropdownOpen(!dropdownOpen)}
        aria-expanded={dropdownOpen}
      >
        <div className="flex items-center truncate">
          <span className="truncate text-sm font-medium group-hover:text-slate-800">{account?.name}</span>
          <svg className="w-3 h-3 shrink-0 ml-1 fill-current text-slate-400" viewBox="0 0 12 12">
            <path d="M5.9 11.4L.5 6l1.4-1.4 4 4 4-4L11.3 6z" />
          </svg>
        </div>
      </button>

      <div
        ref={dropdown}
        onFocus={() => setDropdownOpen(true)}
        onBlur={() => setDropdownOpen(false)}
        className={`origin-top-right z-10 absolute top-full min-w-44 bg-white border border-slate-200 rounded shadow-lg overflow-hidden mt-1 right-0 ${dropdownOpen ? '' : 'hidden'}`}
      >
        {accounts.map((account) =>
          <div
            key={account.id}
            className="py-2 px-3 border-b border-slate-200 cursor-pointer hover:bg-slate-100"
            onClick={() => switchAccount(account)}
          >
            <div className="font-medium text-slate-800">{account.name}</div>
            <div className="text-xs text-slate-500 italic">{account.domain}</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AccountSwitcher;
