import { useRef } from 'react';
import { Link } from 'react-router-dom';
import { useToggle } from '../../hooks/toggle';

import { useCurrentUser } from '../../hooks/user';
import UserAvatar from '../UserAvatar/UserAvatar';

interface UserMenuProps {
}

const UserMenu: React.FunctionComponent<UserMenuProps> = () => {
  const user = useCurrentUser();

  const trigger = useRef<HTMLButtonElement>(null);
  const dropdown = useRef<HTMLDivElement>(null);
  const [dropdownOpen, setDropdownOpen] = useToggle(trigger, dropdown, false);

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
          <UserAvatar user={user} />
        </div>
      </button>

      <div
        ref={dropdown}
        onFocus={() => setDropdownOpen(true)}
        onBlur={() => setDropdownOpen(false)}
        className={`origin-top-right z-10 absolute top-full min-w-44 bg-white border border-slate-200 py-1.5 rounded shadow-lg overflow-hidden mt-1 right-0 ${dropdownOpen ? '' : 'hidden'}`}
      >
        <div className="pt-0.5 pb-2 px-3 mb-1 border-b border-slate-200">
          <div className="font-medium text-slate-800">{user.email}</div>
        </div>
        <ul>
          <li>
            <Link
              className="font-medium text-sm text-indigo-500 hover:text-indigo-600 flex items-center py-1 px-3"
              to="/signin"
              onClick={() => setDropdownOpen(!dropdownOpen)}
            >
              Sign Out
            </Link>
          </li>
        </ul>
      </div>
    </div>
  );
};

export default UserMenu;
