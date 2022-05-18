import { createCache, useCache } from '@react-hook/cache';
import { useEffect, useState } from 'react';

import { APIClient } from '../services/api';

const countriesCache = createCache<{ name: string, alpha_2: string }[]>((async (key: string) => {
  const api = new APIClient();
  const { data } = await api.getOpenAPI();
  const addressSchema = data.components.schemas.Address;
  return addressSchema.properties.country.countries;
}));

export const useCountriesCache = (): [{ name: string, alpha_2: string }[], boolean] => {
  const [{ status, value }, load] = useCache(countriesCache, 'countries');
  const [countries, setCountries] = useState<{ name: string, alpha_2: string }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status === 'idle') {
      load();
      setLoading(true);
    }
  }, [status, load]);

  useEffect(() => {
    if (status === 'success' && value) {
      setCountries(value);
      setLoading(false);
    }
  }, [status, value]);

  return [countries, loading];
};
