import { useTranslation } from 'react-i18next';

export const useFieldRequiredErrorMessage = (): string => {
  const { t } = useTranslation(['common']);
  return t('common_errors.field_required');
};
