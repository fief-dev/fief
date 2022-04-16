import { createCache, useCache } from '@react-hook/cache';
import { Dispatch, useCallback, useEffect, useState } from 'react';

import { APIClient, API_PORT, isAxiosException } from '../services/api';
import * as schemas from '../schemas';

const workspacesCache = createCache<schemas.workspace.WorkspacePublic[]>((async (key: string) => {
  const api = new APIClient();
  try {
    const { data } = await api.listWorkspaces();
    return data.results;
  } catch (err) {
    if (isAxiosException(err)) {
      const response = err.response;
      if (response && (response.status === 401 || response.status === 403)) {
        window.location.href = APIClient.getLoginURL();
      }
    }
  }
}) as (key: string) => Promise<schemas.workspace.WorkspacePublic[]>);

export const useWorkspacesCache = (): [schemas.workspace.WorkspacePublic[], boolean] => {
  const [{ status, value }, load] = useCache(workspacesCache, 'workspaces');
  const [workspaces, setWorkspaces] = useState<schemas.workspace.WorkspacePublic[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status === 'idle') {
      setLoading(true);
      load();
    }
  }, [status, load]);

  useEffect(() => {
    if (status === 'success' && value) {
      setWorkspaces(value);
      setLoading(false);
    }
  }, [status, value]);

  return [workspaces, loading];
};

export const useCurrentWorkspace = (): [schemas.workspace.WorkspacePublic | undefined, boolean, Dispatch<schemas.workspace.WorkspacePublic>] => {
  const [workspaces] = useWorkspacesCache();
  const [currentWorskpaceLoading, setCurrentWorkspaceLoading] = useState(true);
  const [workspace, setWorkspace] = useState<schemas.workspace.WorkspacePublic | undefined>();

  const getWorkspace = useCallback(async () => {
    const workspaceDomain = `${window.location.hostname}${API_PORT ? `:${API_PORT}` : ''}`;
    if (workspaceDomain) {
      return workspaces.find((workspace) => workspace.domain === workspaceDomain);
    }
    return undefined;
  }, [workspaces]);

  useEffect(() => {
    if (!workspace) {
      setCurrentWorkspaceLoading(true);
      getWorkspace().then((workspace) => {
        setWorkspace(workspace);
        setCurrentWorkspaceLoading(false);
      });
    }
  }, [getWorkspace, workspace]);

  return [workspace, currentWorskpaceLoading, setWorkspace];
};
