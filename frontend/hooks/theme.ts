import { useEffect } from 'react';

interface Colors {
  primary?: string;
  primaryHover?: string;
  primaryLight?: string;
}

export const useTenantColors = ({ primary, primaryHover, primaryLight }: Colors) => {
  useEffect(() => {
    if (primary) {
      document.documentElement.style.setProperty('--color-primary', primary);
    }
    if (primaryHover) {
      document.documentElement.style.setProperty('--color-primary-hover', primaryHover);
    }
    if (primaryLight) {
      document.documentElement.style.setProperty('--color-primary-light', primaryLight);
    }
  }, [primary, primaryHover, primaryLight]);
};
