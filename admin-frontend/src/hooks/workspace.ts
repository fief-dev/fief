import { createCache, useCache } from '@react-hook/cache';
import { Dispatch, useCallback, useEffect, useState } from 'react';

import { APIClient, isAxiosException } from '../services/api';
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

export const useCurrentWorkspace = (): [schemas.workspace.WorkspacePublic | undefined, Dispatch<schemas.workspace.WorkspacePublic>] => {
  const [workspaces, loading] = useWorkspacesCache();
  const [workspace, setWorkspace] = useState<schemas.workspace.WorkspacePublic | undefined>();

  const getWorkspace = useCallback(async () => {
    const workspaceDomain = window.location.host;
    let workspace: schemas.workspace.WorkspacePublic | undefined;
    if (workspaceDomain) {
      workspace = workspaces.find((workspace) => workspace.domain === workspaceDomain);
    }
    if (!workspace) {
      workspace = workspaces[0];
    }
    return workspace;
  }, [workspaces]);

  useEffect(() => {
    if (!loading && !workspace) {
      getWorkspace().then((workspace) => {
        setWorkspace(workspace);
      });
    }
  }, [getWorkspace, loading, workspace]);

  return [workspace, setWorkspace];
};
