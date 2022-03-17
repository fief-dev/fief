import { Suspense, useEffect } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';

import './i18n';
import WorkspaceContextProvider from './components/WorkspaceContextProvider/WorkspaceContextProvider';
import UserContextProvider from './components/UserContextProvider/UserContextProvider';
import { useWorkspacesCache } from './hooks/workspace';
import APIKeys from './routes/APIKeys/APIKeys';
import Clients from './routes/Clients/Clients';
import CreateWorkspace from './routes/CreateWorkspace/CreateWorkspace';
import CreateWorkspaceStep1 from './routes/CreateWorkspaceStep1/CreateWorkspaceStep1';
import CreateWorkspaceStep2 from './routes/CreateWorkspaceStep2/CreateWorkspaceStep2';
import CreateWorkspaceStep3 from './routes/CreateWorkspaceStep3/CreateWorkspaceStep3';
import CreateWorkspaceStep4 from './routes/CreateWorkspaceStep4/CreateWorkspaceStep4';
import Dashboard from './routes/Dashboard/Dashboard';
import Tenants from './routes/Tenants/Tenants';
import Users from './routes/Users/Users';

function App() {
  const [workspaces, loading] = useWorkspacesCache();
  const navigate = useNavigate();
  const { pathname } = useLocation();

  useEffect(() => {
    if (!loading && workspaces.length === 0) {
      navigate('/create-workspace');
    }
  }, [loading, workspaces, navigate]);

  useEffect(() => {
    if (pathname === '/create-workspace') {
      navigate('/create-workspace/step1');
    }
  }, [pathname, navigate]);

  return (
    <Suspense fallback="loading">
      <UserContextProvider>
        <WorkspaceContextProvider>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/tenants" element={<Tenants />} />
            <Route path="/clients" element={<Clients />} />
            <Route path="/users" element={<Users />} />
            <Route path="/api-keys" element={<APIKeys />} />
            <Route path="/create-workspace" element={<CreateWorkspace />}>
              <Route path="step1" element={<CreateWorkspaceStep1 />} />
              <Route path="step2" element={<CreateWorkspaceStep2 />} />
              <Route path="step3" element={<CreateWorkspaceStep3 />} />
              <Route path="step4" element={<CreateWorkspaceStep4 />} />
            </Route>
          </Routes>
        </WorkspaceContextProvider>
      </UserContextProvider>
    </Suspense>
  );
}

export default App;
