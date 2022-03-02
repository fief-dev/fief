import { useContext } from 'react';
import { Routes, Route } from 'react-router-dom';

import './i18n';
import AccountContext from './contexts/account';
import Dashboard from './routes/Dashboard/Dashboard';
import Clients from './routes/Clients/Clients';
import CreateAccount from './routes/CreateAccount/CreateAccount';
import Tenants from './routes/Tenants/Tenants';
import Users from './routes/Users/Users';

function Router() {
  const [account] = useContext(AccountContext);

  return (
    <Routes>
      {account &&
        <>
          <Route path="/" element={<Dashboard />} />
          <Route path="/tenants" element={<Tenants />} />
          <Route path="/clients" element={<Clients />} />
          <Route path="/users" element={<Users />} />
        </>
      }
      <Route path="/create-account" element={<CreateAccount />} />
    </Routes>
  );
}

export default Router;
