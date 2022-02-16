import { useMemo } from 'react';
import { Trans, useTranslation } from 'react-i18next';

interface PaginationProps {
  current: number;
  max: number;
  pageSize: number;
  count: number;
  onPageChanged: (page: number) => void;
}

const Pagination: React.FunctionComponent<PaginationProps> = ({ current, max, pageSize, count, onPageChanged }) => {
  const { t } = useTranslation('common');

  const firstIndex = useMemo(() => (current - 1) * pageSize + 1, [current, pageSize]);
  const lastIndex = useMemo(() => current * pageSize, [current, pageSize]);

  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
      <nav className="mb-4 sm:mb-0 sm:order-1" role="navigation" aria-label="Navigation">
        <ul className="flex justify-center">
          <li className="ml-3 first:ml-0">
            <button type="button" className={current === 1 ? 'btn bg-white border-slate-200 text-slate-300 cursor-not-allowed' : 'btn bg-white border-slate-200 hover:border-slate-300 text-indigo-500'} onClick={() => onPageChanged(current - 1)} disabled={current === 1}>&lt;- {t('pagination.previous')}</button>
          </li>
          <li className="ml-3 first:ml-0">
            <button type="button" className={current >= max ? 'btn bg-white border-slate-200 text-slate-300 cursor-not-allowed' : 'btn bg-white border-slate-200 hover:border-slate-300 text-indigo-500'} onClick={() => onPageChanged(current + 1)} disabled={current === max}>{t('pagination.next')} -&gt;</button>
          </li>
        </ul>
      </nav>
      <div className="text-sm text-slate-500 text-center sm:text-left">
        <Trans t={t} i18nKey="pagination.showing" transKeepBasicHtmlNodesFor={['span']} values={{ firstIndex, lastIndex }} count={count}>
        <span className="font-medium text-slate-600">{firstIndex}</span>
        <span className="font-medium text-slate-600">{lastIndex}</span>
        <span className="font-medium text-slate-600">{count}</span>
        </Trans>
      </div>
    </div>
  );
};

export default Pagination;
