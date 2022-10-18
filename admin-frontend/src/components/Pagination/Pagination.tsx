import { useMemo } from 'react';
import { Trans, useTranslation } from 'react-i18next';
import { ArrowLeftIcon, ArrowRightIcon } from '@heroicons/react/20/solid';


interface PaginationProps {
  current: number;
  max: number;
  pageSize: number;
  count: number;
  onPageChanged: (page: number) => void;
}

const Pagination: React.FunctionComponent<React.PropsWithChildren<PaginationProps>> = ({ current, max, pageSize, count, onPageChanged }) => {
  const { t } = useTranslation('common');

  const firstIndex = useMemo(() => (current - 1) * pageSize + 1, [current, pageSize]);
  const lastIndex = useMemo(() => current * pageSize, [current, pageSize]);

  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
      <nav className="mb-4 sm:mb-0 sm:order-1" role="navigation" aria-label="Navigation">
        <ul className="flex justify-center">
          <li className="ml-3 first:ml-0">
            <button type="button" className={`flex items-center ${current === 1 ? 'btn bg-white border-slate-200 text-slate-300 cursor-not-allowed' : 'btn bg-white border-slate-200 hover:border-slate-300 text-primary-500'}`} onClick={() => onPageChanged(current - 1)} disabled={current === 1}>
              <ArrowLeftIcon width={12} height={12} className="mr-1" />
              {t('pagination.previous')}
            </button>
          </li>
          <li className="ml-3 first:ml-0">
            <button type="button" className={`flex items-center ${current >= max ? 'btn bg-white border-slate-200 text-slate-300 cursor-not-allowed' : 'btn bg-white border-slate-200 hover:border-slate-300 text-primary-500'}`} onClick={() => onPageChanged(current + 1)} disabled={current === max}>
              {t('pagination.next')}
              <ArrowRightIcon width={12} height={12} className="ml-1" />
            </button>
          </li>
        </ul>
      </nav>
      <div className="text-sm text-slate-500 text-center sm:text-left">
        <Trans
          t={t}
          i18nKey="pagination.showing"
          components={{ format: <span className="font-medium text-slate-600" /> }}
          values={{ firstIndex, lastIndex }}
          count={count}
        />
      </div>
    </div>
  );
};

export default Pagination;
