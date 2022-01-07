import { useTranslation } from 'next-i18next';

export const useFieldRequiredErrorMessage = (): string => {
  const { t } = useTranslation('common');
  return t('common_errors.field_required');
};
