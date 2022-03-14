import { Suspense, useEffect } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';

import './i18n';
import AccountContextProvider from './components/AccountContextProvider/AccountContextProvider';
import UserContextProvider from './components/UserContextProvider/UserContextProvider';
import { useAccountsCache } from './hooks/account';
import APIKeys from './routes/APIKeys/APIKeys';
import Clients from './routes/Clients/Clients';
import CreateAccount from './routes/CreateAccount/CreateAccount';
import CreateAccountStep1 from './routes/CreateAccountStep1/CreateAccountStep1';
import CreateAccountStep2 from './routes/CreateAccountStep2/CreateAccountStep2';
import CreateAccountStep3 from './routes/CreateAccountStep3/CreateAccountStep3';
import CreateAccountStep4 from './routes/CreateAccountStep4/CreateAccountStep4';
import Dashboard from './routes/Dashboard/Dashboard';
import Tenants from './routes/Tenants/Tenants';
import Users from './routes/Users/Users';

function App() {
  const [accounts, loading] = useAccountsCache();
  const navigate = useNavigate();
  const { pathname } = useLocation();

  useEffect(() => {
    if (!loading && accounts.length === 0) {
      navigate('/create-account');
    }
  }, [loading, accounts, navigate]);

  useEffect(() => {
    if (pathname === '/create-account') {
      navigate('/create-account/step1');
    }
  }, [pathname, navigate]);

  return (
    <Suspense fallback="loading">
      <UserContextProvider>
        <AccountContextProvider>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/tenants" element={<Tenants />} />
            <Route path="/clients" element={<Clients />} />
            <Route path="/users" element={<Users />} />
            <Route path="/api-keys" element={<APIKeys />} />
            <Route path="/create-account" element={<CreateAccount />}>
              <Route path="step1" element={<CreateAccountStep1 />} />
              <Route path="step2" element={<CreateAccountStep2 />} />
              <Route path="step3" element={<CreateAccountStep3 />} />
              <Route path="step4" element={<CreateAccountStep4 />} />
            </Route>
          </Routes>
        </AccountContextProvider>
      </UserContextProvider>
    </Suspense>
  );
}

export default App;
