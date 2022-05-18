import { createCache, useCache } from '@react-hook/cache';
import { useEffect, useState } from 'react';

import { APIClient } from '../services/api';

const timezonesCache = createCache<string[]>((async (key: string) => {
  const api = new APIClient();
  const { data } = await api.getOpenAPI();
  const userFieldConfigurationSchema = data.components.schemas.UserFieldConfiguration;
  const defaultFieldTypes: Record<string, any>[] = userFieldConfigurationSchema.properties.default.anyOf;
  const timezoneType = defaultFieldTypes.find((type) => type.title === 'timezone');
  return timezoneType?.enum || [];
}));

export const useTimezonesCache = (): [string[], boolean] => {
  const [{ status, value }, load] = useCache(timezonesCache, 'timezones');
  const [timezones, setTimezones] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status === 'idle') {
      load();
      setLoading(true);
    }
  }, [status, load]);

  useEffect(() => {
    if (status === 'success' && value) {
      setTimezones(value);
      setLoading(false);
    }
  }, [status, value]);

  return [timezones, loading];
};
