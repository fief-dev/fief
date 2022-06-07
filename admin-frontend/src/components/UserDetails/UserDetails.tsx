import { useState } from 'react';
import { useTranslation } from 'react-i18next';

import * as schemas from '../../schemas';
import UserDetailsAccount from '../UserDetailsAccount/UserDetailsAccount';
import UserDetailsPermissions from '../UserDetailsPermissions/UserDetailsPermissions';
import UserDetailsRoles from '../UserDetailsRoles/UserDetailsRoles';

enum UserDetailsTab {
  ACCOUNT = 'ACCOUNT',
  ROLES = 'ROLES',
  PERMISSIONS = 'PERMISSIONS',
}

interface UserDetailsProps {
  user: schemas.user.User;
  onUpdated?: (client: schemas.user.User) => void;
}

const UserDetails: React.FunctionComponent<React.PropsWithChildren<UserDetailsProps>> = ({ user, onUpdated }) => {
  const { t } = useTranslation(['users']);
  const [currentTab, setCurrentTab] = useState<UserDetailsTab>(UserDetailsTab.ACCOUNT);

  return (
    <>
      <div className="text-slate-800 font-semibold text-center mb-6">{user.email}</div>
      <div className="relative mb-8">
        <div className="absolute bottom-0 w-full h-px bg-slate-200" aria-hidden="true"></div>
        <ul className="relative text-sm font-medium flex flex-nowrap -mx-4 sm:-mx-6 lg:-mx-8 overflow-x-scroll no-scrollbar">
          {Object.values(UserDetailsTab).map((tab) =>
            <li className="mr-6 last:mr-0 first:pl-4 sm:first:pl-6 lg:first:pl-8 last:pr-4 sm:last:pr-6 lg:last:pr-8">
              <button
                className={`block pb-3 whitespace-nowrap ${tab === currentTab ? 'text-primary-500 border-primary-500 border-b-2' : 'text-slate-500 hover:text-slate-600'}`}
                onClick={() => setCurrentTab(tab)}
              >
                {t(`details.tabs.${tab}`)}
              </button>
            </li>
          )}
        </ul>
      </div>
      {currentTab === UserDetailsTab.ACCOUNT && <UserDetailsAccount user={user} onUpdated={onUpdated} />}
      {currentTab === UserDetailsTab.ROLES && <UserDetailsRoles user={user} />}
      {currentTab === UserDetailsTab.PERMISSIONS && <UserDetailsPermissions user={user} />}
    </>
  );
};

export default UserDetails;
