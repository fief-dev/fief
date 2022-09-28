import { Suspense, useEffect, useMemo } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';

import './i18n';
import DBConnectionErrorAlert from './components/DBConnectionErrorAlert/DBConnectionErrorAlert';
import LoadingScreen from './components/LoadingScreen/LoadingScreen';
import UserContextProvider from './components/UserContextProvider/UserContextProvider';
import UserFieldsSelectionContextProvider from './components/UserFieldsSelectionContextProvider/UserFieldsSelectionContextProvider';
import WorkspaceContextProvider from './components/WorkspaceContextProvider/WorkspaceContextProvider';
import APIClientContext from './contexts/api';
import { useCurrentWorkspace, useWorkspacesCache } from './hooks/workspace';
import APIKeys from './routes/APIKeys/APIKeys';
import Clients from './routes/Clients/Clients';
import CreateWorkspace from './routes/CreateWorkspace/CreateWorkspace';
import CreateWorkspaceStep1 from './routes/CreateWorkspaceStep1/CreateWorkspaceStep1';
import CreateWorkspaceStep2 from './routes/CreateWorkspaceStep2/CreateWorkspaceStep2';
import CreateWorkspaceStep3 from './routes/CreateWorkspaceStep3/CreateWorkspaceStep3';
import CreateWorkspaceStep4 from './routes/CreateWorkspaceStep4/CreateWorkspaceStep4';
import Dashboard from './routes/Dashboard/Dashboard';
import OAuthProviders from './routes/OAuthProviders/OAuthProviders';
import Permissions from './routes/Permissions/Permissions';
import Roles from './routes/Roles/Roles';
import SelectWorkspace from './routes/SelectWorkspace/SelectWorkspace';
import Tenants from './routes/Tenants/Tenants';
import Users from './routes/Users/Users';
import UserFields from './routes/UserFields/UserFields';
import { APIClient } from './services/api';

function App() {
  const [workspaces, loading] = useWorkspacesCache();
  const [currentWorkspace, currentWorkspaceLoading] = useCurrentWorkspace();
  const api = useMemo(() => new APIClient(), []);
  const navigate = useNavigate();
  const { pathname } = useLocation();

  useEffect(() => {
    if (pathname === '/create-workspace') {
      navigate('/create-workspace/step1', { replace: true });
    } else if (!loading && !currentWorkspaceLoading && !pathname.startsWith('/create-workspace')) {
      if (workspaces.length === 0) {
        navigate('/create-workspace');
      } else if (!currentWorkspace) {
        navigate('/select-workspace');
      }
    }
  }, [pathname, loading, workspaces, currentWorkspace, currentWorkspaceLoading, navigate]);

  return (
    <Suspense fallback={<LoadingScreen />}>
      <APIClientContext.Provider value={api}>
        <UserContextProvider>
          <WorkspaceContextProvider>
            <DBConnectionErrorAlert />
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/tenants" element={<Tenants />} />
              <Route path="/clients" element={<Clients />} />
              <Route path="/oauth-providers" element={<OAuthProviders />} />
              <Route path="/users" element={<UserFieldsSelectionContextProvider><Users /></UserFieldsSelectionContextProvider>} />
              <Route path="/user-fields" element={<UserFields />} />
              <Route path="/permissions" element={<Permissions />} />
              <Route path="/roles" element={<Roles />} />
              <Route path="/api-keys" element={<APIKeys />} />
              <Route path="/select-workspace" element={<SelectWorkspace />} />
              <Route path="/create-workspace" element={<CreateWorkspace />}>
                <Route path="step1" element={<CreateWorkspaceStep1 />} />
                <Route path="step2" element={<CreateWorkspaceStep2 />} />
                <Route path="step3" element={<CreateWorkspaceStep3 />} />
                <Route path="step4" element={<CreateWorkspaceStep4 />} />
              </Route>
            </Routes>
          </WorkspaceContextProvider>
        </UserContextProvider>
      </APIClientContext.Provider>
    </Suspense>
  );
}

export default App;
