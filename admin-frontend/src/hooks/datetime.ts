import { useMemo } from 'react';

export const formatDateTime = (datetime: string | Date, displayTime: boolean): string => {
  return new Date(datetime).toLocaleString(
    undefined,
    {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      ...displayTime ? { hour: '2-digit', minute: '2-digit' } : {},
    },
  );
};

export const useFormattedDateTime = (datetime: string | Date, displayTime: boolean): string => {
  return useMemo(() => formatDateTime(datetime, displayTime), [datetime, displayTime]);
};
